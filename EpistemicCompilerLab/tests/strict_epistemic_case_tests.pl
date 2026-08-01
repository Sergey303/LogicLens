:- begin_tests(strict_epistemic_case).

:- use_module('../prolog/strict_epistemic_case').

test(supported_case) :-
    case_frame(rx1, mx1, p1, none, Frame),
    get_dict(status, Frame, supported),
    get_dict(evidence, Frame, [p1]).

test(refuted_case) :-
    case_frame(rx2, mx2, none, n1, Frame),
    get_dict(status, Frame, refuted),
    get_dict(evidence, Frame, [n1]).

test(unknown_case) :-
    case_frame(rx3, mx3, none, none, Frame),
    get_dict(status, Frame, unknown),
    get_dict(evidence, Frame, []).

test(conflicting_case) :-
    case_frame(rx4, mx4, p2, n2, Frame),
    get_dict(status, Frame, conflicting),
    get_dict(action, Frame, report_conflict),
    get_dict(evidence, Frame, [n2,p2]).

test(multiple_evidence_ids) :-
    case_frame(rx5, mx5, 'p3,p4', 'n3,n4', Frame),
    get_dict(evidence, Frame, [n3,n4,p3,p4]).

test(missing_revision) :-
    case_frame(missing, mx6, none, none, Frame),
    get_dict(status, Frame, not_evaluated),
    get_dict(askField, Frame, revision).

test(missing_material) :-
    case_frame(rx7, missing, none, none, Frame),
    get_dict(status, Frame, not_evaluated),
    get_dict(askField, Frame, material).

:- end_tests(strict_epistemic_case).
