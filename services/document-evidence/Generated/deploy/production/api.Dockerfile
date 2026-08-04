ARG DOTNET_SDK_IMAGE=mcr.microsoft.com/dotnet/sdk:10.0
ARG DOTNET_ASPNET_IMAGE=mcr.microsoft.com/dotnet/aspnet:10.0

FROM ${DOTNET_SDK_IMAGE} AS build
ARG APPFORGE_GENERATED_PROJECT=backend/DocumentEvidenceOperationalModel.Persistence.csproj
WORKDIR /src
COPY . .
RUN dotnet publish "$APPFORGE_GENERATED_PROJECT" -c Release -o /out /p:UseAppHost=false

FROM ${DOTNET_ASPNET_IMAGE} AS runtime
ARG APPFORGE_ASSEMBLY=DocumentEvidenceOperationalModel.Persistence.dll
ENV ASPNETCORE_URLS=http://+:8080 \
    DOTNET_RUNNING_IN_CONTAINER=true \
    APPFORGE_ASSEMBLY=$APPFORGE_ASSEMBLY
WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 64198 appforge \
    && useradd --uid 64198 --gid appforge --home-dir /app --shell /usr/sbin/nologin appforge
COPY --from=build /out ./
RUN mkdir -p /app/data \
    && chown -R appforge:appforge /app
VOLUME ["/app/data"]
USER appforge
EXPOSE 8080
ENTRYPOINT ["sh", "-c", "exec dotnet \"$APPFORGE_ASSEMBLY\" \"$@\"", "--"]
