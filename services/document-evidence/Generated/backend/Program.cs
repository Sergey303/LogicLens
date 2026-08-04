#nullable enable

using System.Net;
using System.Security.Claims;
using System.Text;
using System.Threading.RateLimiting;
using LogicLens.DocumentEvidence.Generated.Api.Contracts;
using LogicLens.DocumentEvidence.Generated.Api.Services;
using LogicLens.DocumentEvidence.Generated.Auth;
using LogicLens.DocumentEvidence.Generated.Persistence;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.AspNetCore.RateLimiting;
using Microsoft.EntityFrameworkCore;

const string AppForgeAuthenticationScheme = "AppForgeGenerated";
const string AppForgeProductionCorsPolicy = "AppForgeProductionCors";
const string AppForgeApiRateLimitPolicy = "AppForgeApiLimiter";

var appForgeMigrateOnly = args.Contains("--appforge-migrate-only", StringComparer.OrdinalIgnoreCase);
var appForgeSeedOnly = args.Contains("--appforge-seed-only", StringComparer.OrdinalIgnoreCase);
var builder = WebApplication.CreateBuilder(args);
if (builder.Configuration.GetValue<bool>("Production:ApplyMigrationsOnStartup"))
{
    throw new InvalidOperationException("Production startup must not apply migrations automatically. Run with --appforge-migrate-only or --appforge-seed-only as a controlled deployment step.");
}
ValidateProductionEmailTransport(builder.Configuration);
builder.Logging.ClearProviders();
builder.Logging.AddJsonConsole(options =>
{
    options.IncludeScopes = true;
    options.TimestampFormat = "O";
});
var forwardedHeadersOptions = BuildForwardedHeadersOptions(builder.Configuration);
var contentSecurityPolicy = builder.Configuration["SecurityHeaders:ContentSecurityPolicy"]
    ?? "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; object-src 'none'; form-action 'self'";
var allowedOrigins = builder.Configuration.GetSection("Cors:AllowedOrigins").Get<string[]>()?
    .Select(origin => origin.Trim())
    .Where(origin => origin.Length > 0)
    .Select(origin => origin.TrimEnd('/'))
    .Distinct(StringComparer.OrdinalIgnoreCase)
    .ToArray() ?? [];
if (allowedOrigins.Length == 0)
{
    throw new InvalidOperationException("Production requires Cors:AllowedOrigins.");
}

if (allowedOrigins.Any(origin => origin == "*" || origin.Contains('*', StringComparison.Ordinal)))
{
    throw new InvalidOperationException("Production Cors:AllowedOrigins must be explicit and must not contain '*'.");
}
ValidateProductionCorsOrigins(allowedOrigins);

var requestBodyLimitBytes = builder.Configuration.GetValue<long?>("RequestLimits:RequestBodyLimitBytes")
    ?? builder.Configuration.GetValue<long?>("RequestLimits:MultipartBodyLengthLimitBytes")
    ?? 10 * 1024 * 1024;
var multipartBodyLimitBytes = builder.Configuration.GetValue<long?>("RequestLimits:MultipartBodyLengthLimitBytes")
    ?? requestBodyLimitBytes;

builder.Services.AddCors(options =>
{
    options.AddPolicy(
        AppForgeProductionCorsPolicy,
        policy => policy.WithOrigins(allowedOrigins).AllowAnyHeader().AllowAnyMethod().AllowCredentials());
});

builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    options.AddPolicy(AppForgeApiRateLimitPolicy, httpContext =>
        RateLimitPartition.GetFixedWindowLimiter(
            ResolveRateLimitPartitionKey(httpContext),
            _ => BuildRateLimiterOptions(builder.Configuration, "RateLimiting:Api", 120, TimeSpan.FromMinutes(1))));
});

builder.Services.Configure<Microsoft.AspNetCore.Http.Features.FormOptions>(options =>
{
    options.MultipartBodyLengthLimit = multipartBodyLimitBytes;
    options.ValueLengthLimit = builder.Configuration.GetValue<int?>("RequestLimits:FormValueLengthLimitBytes") ?? 64 * 1024;
    options.ValueCountLimit = builder.Configuration.GetValue<int?>("RequestLimits:FormValueCountLimit") ?? 128;
});

builder.Services.AddHttpContextAccessor();
builder.Services.AddAppForgeEmail(builder.Configuration, emailFeaturesEnabled: true, isProduction: true);
builder.Services.AddScoped<IdentityAuditService>();
builder.Services.AddScoped<AuthLoginService>();
builder.Services.AddScoped<AuthTokenService>();
builder.Services.AddScoped<AdminUserService>();
builder.Services.AddControllers(options =>
{
    options.Filters.Add(new Microsoft.AspNetCore.Mvc.RequestSizeLimitAttribute(requestBodyLimitBytes));
});
builder.Services
    .AddAuthentication(AppForgeAuthenticationScheme)
    .AddScheme<AuthenticationSchemeOptions, AppForgeBearerAuthenticationHandler>(
        AppForgeAuthenticationScheme,
        _ => { });
builder.Services.AddAuthorization();
builder.Services.AddDbContext<DocumentEvidenceOperationalModelDbContext>(options =>
{
    var connectionString = builder.Configuration.GetConnectionString("Default");
    if (string.IsNullOrWhiteSpace(connectionString))
    {
        throw new InvalidOperationException("Production requires ConnectionStrings:Default.");
    }
    options.UseNpgsql(connectionString);
});
builder.Services.AddScoped<DocumentService>();
builder.Services.AddScoped<StoredObjectService>();
builder.Services.AddScoped<DocumentRevisionService>();
builder.Services.AddScoped<ProcessingJobService>();
builder.Services.AddScoped<DocumentFragmentService>();
builder.Services.AddScoped<RoleService>();
builder.Services.AddScoped<PermissionService>();
builder.Services.AddScoped<RolePermissionService>();
builder.Services.AddScoped<StaffPositionService>();
builder.Services.AddScoped<StaffPositionRoleService>();
builder.Services.AddScoped<StaffPositionAssignmentService>();

var app = builder.Build();
var appForgeMetrics = new AppForgeRuntimeMetrics();

if (appForgeMigrateOnly || appForgeSeedOnly)
{
    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<DocumentEvidenceOperationalModelDbContext>();
    await db.Database.MigrateAsync(CancellationToken.None);
    if (appForgeSeedOnly)
    {
        await AuthSeedService.SeedAsync(db, builder.Configuration, CancellationToken.None);
    }
    return;
}

app.UseForwardedHeaders(forwardedHeadersOptions);
app.UseHsts();
app.Use(next =>
{
    return async context =>
    {
        context.Response.OnStarting(() =>
        {
            var headers = context.Response.Headers;
            headers["X-Content-Type-Options"] = "nosniff";
            headers["X-Frame-Options"] = "DENY";
            headers["Referrer-Policy"] = "no-referrer";
            headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()";
            if (!string.IsNullOrWhiteSpace(contentSecurityPolicy))
            {
                headers["Content-Security-Policy"] = contentSecurityPolicy;
            }
            return Task.CompletedTask;
        });
        await next(context);
    };
});
app.UseExceptionHandler(exceptionApp =>
{
    exceptionApp.Run(async context =>
    {
        context.Response.StatusCode = StatusCodes.Status500InternalServerError;
        context.Response.ContentType = "application/problem+json";
        await context.Response.WriteAsync("{\"type\":\"about:blank\",\"title\":\"An unexpected error occurred.\",\"status\":500}");
    });
});
app.Use(next =>
{
    return async context =>
    {
        var requestPath = context.Request.Path;
        if (requestPath.Equals("/metrics", StringComparison.OrdinalIgnoreCase)
            || requestPath.Equals("/health/live", StringComparison.OrdinalIgnoreCase)
            || requestPath.Equals("/health/ready", StringComparison.OrdinalIgnoreCase))
        {
            await next(context);
            return;
        }

        await appForgeMetrics.TrackAsync(context, next);
    };
});
app.UseCors(AppForgeProductionCorsPolicy);
app.UseAuthentication();
app.UseRateLimiter();
app.UseAuthorization();
app.MapControllers().RequireRateLimiting(AppForgeApiRateLimitPolicy);
app.MapGet("/health/live", () => Results.Ok(new { status = "live" }));
app.MapGet("/health/ready", async (DocumentEvidenceOperationalModelDbContext db, CancellationToken ct) =>
{
    try
    {
        return await db.Database.CanConnectAsync(ct)
            ? Results.Ok(new { status = "ready" })
            : Results.StatusCode(StatusCodes.Status503ServiceUnavailable);
    }
    catch
    {
        return Results.StatusCode(StatusCodes.Status503ServiceUnavailable);
    }
});
app.MapGet("/metrics", () => Results.Text(appForgeMetrics.RenderPrometheus(), "text/plain; version=0.0.4; charset=utf-8"))
    .RequireRateLimiting(AppForgeApiRateLimitPolicy);

app.Run();

static void ValidateProductionCorsOrigins(IReadOnlyList<string> origins)
{
    foreach (var origin in origins)
    {
        if (!Uri.TryCreate(origin, UriKind.Absolute, out var uri) || !uri.Scheme.Equals(Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase))
        {
            throw new InvalidOperationException("Production Cors:AllowedOrigins entries must be absolute HTTPS origins.");
        }

        if (!string.IsNullOrWhiteSpace(uri.UserInfo) || !string.IsNullOrWhiteSpace(uri.Fragment))
        {
            throw new InvalidOperationException("Production Cors:AllowedOrigins entries must be origins only, without user info or fragment.");
        }

        if (!string.IsNullOrWhiteSpace(uri.PathAndQuery) && uri.PathAndQuery != "/")
        {
            throw new InvalidOperationException("Production Cors:AllowedOrigins entries must be origins only, without path or query.");
        }
    }
}

static void ValidateProductionEmailTransport(IConfiguration configuration)
{
    var mode = configuration["AppForge:Email:Mode"] ?? "Disabled";
    if (!mode.Equals("Smtp", StringComparison.OrdinalIgnoreCase))
    {
        return;
    }

    if (configuration.GetValue<bool?>("AppForge:Email:Smtp:EnableSsl") != true)
    {
        throw new InvalidOperationException("Production SMTP transport requires AppForge:Email:Smtp:EnableSsl=true.");
    }

    var publicBaseUrl = configuration["AppForge:Email:Templates:PublicBaseUrl"];
    if (!string.IsNullOrWhiteSpace(publicBaseUrl)
        && (!Uri.TryCreate(publicBaseUrl, UriKind.Absolute, out var publicUri)
            || !publicUri.Scheme.Equals(Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase)))
    {
        throw new InvalidOperationException("Production email action links require AppForge:Email:Templates:PublicBaseUrl to be an absolute HTTPS URL.");
    }
}

static ForwardedHeadersOptions BuildForwardedHeadersOptions(IConfiguration configuration)
{
    var knownProxyValues = ReadConfiguredList(configuration, "ForwardedHeaders:KnownProxies");
    var knownNetworkValues = ReadConfiguredList(configuration, "ForwardedHeaders:KnownNetworks");
    if (knownProxyValues.Length == 0 && knownNetworkValues.Length == 0)
    {
        throw new InvalidOperationException("Production requires ForwardedHeaders:KnownProxies or ForwardedHeaders:KnownNetworks.");
    }

    var options = new ForwardedHeadersOptions
    {
        ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto | ForwardedHeaders.XForwardedHost,
        ForwardLimit = 1,
    };
    options.KnownProxies.Clear();
    options.KnownIPNetworks.Clear();

    foreach (var proxy in knownProxyValues)
    {
        if (!IPAddress.TryParse(proxy, out var proxyAddress))
        {
            throw new InvalidOperationException("ForwardedHeaders:KnownProxies entries must be valid IP addresses.");
        }

        options.KnownProxies.Add(proxyAddress);
    }

    foreach (var network in knownNetworkValues)
    {
        options.KnownIPNetworks.Add(ParseKnownNetwork(network));
    }

    return options;
}

static string[] ReadConfiguredList(IConfiguration configuration, string sectionName)
{
    return configuration.GetSection(sectionName).Get<string[]>()?
        .Select(value => value.Trim())
        .Where(value => value.Length > 0)
        .Distinct(StringComparer.OrdinalIgnoreCase)
        .ToArray() ?? [];
}

static System.Net.IPNetwork ParseKnownNetwork(string value)
{
    if (!System.Net.IPNetwork.TryParse(value, out var network))
    {
        throw new InvalidOperationException("ForwardedHeaders:KnownNetworks entries must use valid CIDR notation, for example 172.16.0.0/12.");
    }

    return network;
}

static FixedWindowRateLimiterOptions BuildRateLimiterOptions(
    IConfiguration configuration,
    string sectionName,
    int defaultPermitLimit,
    TimeSpan defaultWindow)
{
    var section = configuration.GetSection(sectionName);
    var windowSeconds = section.GetValue<int?>("WindowSeconds") ?? (int)defaultWindow.TotalSeconds;
    return new FixedWindowRateLimiterOptions
    {
        PermitLimit = section.GetValue<int?>("PermitLimit") ?? defaultPermitLimit,
        Window = TimeSpan.FromSeconds(Math.Max(1, windowSeconds)),
        QueueLimit = section.GetValue<int?>("QueueLimit") ?? 0,
        QueueProcessingOrder = QueueProcessingOrder.OldestFirst,
        AutoReplenishment = true,
    };
}

static string ResolveRateLimitPartitionKey(HttpContext context)
{
    var userId = context.User.FindFirstValue(ClaimTypes.NameIdentifier) ?? context.User.FindFirstValue("sub");
    if (!string.IsNullOrWhiteSpace(userId))
    {
        return "user:" + userId;
    }

    return "ip:" + (context.Connection.RemoteIpAddress?.ToString() ?? "unknown");
}

sealed class AppForgeRuntimeMetrics
{
    private long _requestsTotal;
    private long _requestsInFlight;
    private long _requestDurationMsTotal;
    private long _responses2xxTotal;
    private long _responses3xxTotal;
    private long _responses4xxTotal;
    private long _responses5xxTotal;
    private long _exceptionsTotal;

    public async Task TrackAsync(HttpContext context, RequestDelegate next)
    {
        var logger = context.RequestServices.GetRequiredService<ILoggerFactory>().CreateLogger("AppForgeRuntimeRequests");
        var startedAt = TimeProvider.System.GetTimestamp();
        var requestFailed = false;
        Interlocked.Increment(ref _requestsTotal);
        Interlocked.Increment(ref _requestsInFlight);
        try
        {
            await next(context);
        }
        catch (Exception ex)
        {
            requestFailed = true;
            Interlocked.Increment(ref _exceptionsTotal);
            logger.LogError(ex, "HTTP request failed. method={Method} exceptionType={ExceptionType}", context.Request.Method, ex.GetType().Name);
            throw;
        }
        finally
        {
            var elapsed = TimeProvider.System.GetElapsedTime(startedAt);
            var statusCode = requestFailed && context.Response.StatusCode < StatusCodes.Status500InternalServerError
                ? StatusCodes.Status500InternalServerError
                : context.Response.StatusCode;
            Interlocked.Add(ref _requestDurationMsTotal, (long)Math.Round(elapsed.TotalMilliseconds));
            Interlocked.Decrement(ref _requestsInFlight);
            IncrementStatusBucket(statusCode);
            logger.LogInformation(
                "HTTP request completed. method={Method} statusCode={StatusCode} elapsedMs={ElapsedMs}",
                context.Request.Method,
                statusCode,
                Math.Round(elapsed.TotalMilliseconds, 3));
        }
    }

    public string RenderPrometheus()
    {
        var builder = new StringBuilder();
        builder.AppendLine("# HELP appforge_http_requests_total Total HTTP requests observed by AppForge runtime.");
        builder.AppendLine("# TYPE appforge_http_requests_total counter");
        builder.AppendLine($"appforge_http_requests_total {Interlocked.Read(ref _requestsTotal)}");
        builder.AppendLine("# HELP appforge_http_requests_in_flight Current in-flight HTTP requests observed by AppForge runtime.");
        builder.AppendLine("# TYPE appforge_http_requests_in_flight gauge");
        builder.AppendLine($"appforge_http_requests_in_flight {Interlocked.Read(ref _requestsInFlight)}");
        builder.AppendLine("# HELP appforge_http_request_duration_ms_total Sum of HTTP request durations in milliseconds.");
        builder.AppendLine("# TYPE appforge_http_request_duration_ms_total counter");
        builder.AppendLine($"appforge_http_request_duration_ms_total {Interlocked.Read(ref _requestDurationMsTotal)}");
        AppendStatusMetric(builder, "2xx", _responses2xxTotal);
        AppendStatusMetric(builder, "3xx", _responses3xxTotal);
        AppendStatusMetric(builder, "4xx", _responses4xxTotal);
        AppendStatusMetric(builder, "5xx", _responses5xxTotal);
        builder.AppendLine("# HELP appforge_http_exceptions_total Total unhandled exceptions observed by AppForge runtime.");
        builder.AppendLine("# TYPE appforge_http_exceptions_total counter");
        builder.AppendLine($"appforge_http_exceptions_total {Interlocked.Read(ref _exceptionsTotal)}");
        return builder.ToString();
    }

    private void IncrementStatusBucket(int statusCode)
    {
        if (statusCode >= 200 && statusCode <= 299)
        {
            Interlocked.Increment(ref _responses2xxTotal);
        }
        else if (statusCode >= 300 && statusCode <= 399)
        {
            Interlocked.Increment(ref _responses3xxTotal);
        }
        else if (statusCode >= 400 && statusCode <= 499)
        {
            Interlocked.Increment(ref _responses4xxTotal);
        }
        else if (statusCode >= 500)
        {
            Interlocked.Increment(ref _responses5xxTotal);
        }
    }

    private static void AppendStatusMetric(StringBuilder builder, string bucket, long value)
    {
        builder.AppendLine($"appforge_http_responses_total{{status_class=\"{bucket}\"}} {Interlocked.Read(ref value)}");
    }
}
