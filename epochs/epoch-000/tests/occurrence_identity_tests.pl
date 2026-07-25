:- begin_tests(occurrence_identity_v1).

:- use_module('../rules/occurrence_identity.pl').


test(root_person_vector) :-
    occurrence_identity:occurrence_identity(
        'urn:logiclens:person:alex',
        [],
        OccurrenceId,
        CanonicalHex
    ),
    assertion(OccurrenceId == 'o:sha256:9892029c35cacef35d34c23f38394c4f147ab61dec58c73b0c26057141a4c881'),
    assertion(CanonicalHex == '4c6f6769634c656e734f6363757272656e63650001000000000000001975726e3a6c6f6769636c656e733a706572736f6e3a616c6578').


test(person_participation_vector) :-
    occurrence_identity:occurrence_identity(
        'urn:logiclens:person:alex',
        [step(
            'f:sha256:b0a5e5a69a3150e22a03e67cd709be47d8cb7319d6dc8b0cdc574cc0a582c2b3',
            incoming
        )],
        OccurrenceId,
        CanonicalHex
    ),
    assertion(OccurrenceId == 'o:sha256:f01e1dc555c9969bb81e4cf8b67c55530621498e8104a2a70b13aeaa09e2f869'),
    assertion(CanonicalHex == '4c6f6769634c656e734f6363757272656e63650001000000000000001975726e3a6c6f6769636c656e733a706572736f6e3a616c65780000000000000049663a7368613235363a6230613565356136396133313530653232613033653637636437303962653437643863623733313964366463386230636463353734636330613538326332623302').


test(person_participation_iis_vector) :-
    occurrence_identity:occurrence_identity(
        'urn:logiclens:person:alex',
        [
            step(
                'f:sha256:b0a5e5a69a3150e22a03e67cd709be47d8cb7319d6dc8b0cdc574cc0a582c2b3',
                incoming
            ),
            step(
                'f:sha256:9aa0dad76c25bdbbfde243a82b134e70a562d4843863f55dd1300dd1384955e5',
                outgoing
            )
        ],
        OccurrenceId,
        _
    ),
    assertion(OccurrenceId == 'o:sha256:fe5b8e79cc9abe39cb85c1cfd644a9cc6765a25489dabba9be69741805db8dfb').


test(person_student_iis_vector) :-
    occurrence_identity:occurrence_identity(
        'urn:logiclens:person:alex',
        [
            step(
                'f:sha256:dc9fc03281438f6392211a8c1d649b335031a75067c06438270cec98bd17c743',
                incoming
            ),
            step(
                'f:sha256:7d5f4f25c4a067b148920e1d40b3231f2aa8d5513af26f4b5db7e1a70ca92524',
                outgoing
            )
        ],
        OccurrenceId,
        _
    ),
    assertion(OccurrenceId == 'o:sha256:1e52067cf824aa7e73935434ad5d5fa742b34d4687bdd318d069d50d432f84b5').


test(lab_archive_cycle_vector) :-
    occurrence_identity:occurrence_identity(
        'urn:logiclens:org:lab',
        [
            step(
                'f:sha256:da7efc8f8b338f0359030c79558cc7f5d0b3202b35cc47372af32844ad53abae',
                outgoing
            ),
            step(
                'f:sha256:103c4643323d4734463d29f8b788e5f051b297f3c49735e7dad3dc341e4b3358',
                outgoing
            )
        ],
        OccurrenceId,
        _
    ),
    assertion(OccurrenceId == 'o:sha256:f9196db5e8b7a1f53c9e709c38962a543c30feb9ff85e1a73e57eaaf85844280').


:- end_tests(occurrence_identity_v1).
