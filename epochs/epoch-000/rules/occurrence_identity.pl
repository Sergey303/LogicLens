:- module(occurrence_identity, [
    occurrence_identity/4,
    occurrence_bytes/3
]).

:- use_module(library(crypto)).
:- use_module(library(utf8)).


occurrence_identity(Root, Steps, OccurrenceId, CanonicalHex) :-
    occurrence_bytes(Root, Steps, Bytes),
    crypto_data_hash(
        Bytes,
        Hash,
        [algorithm(sha256), encoding(octet)]
    ),
    atom_concat('o:sha256:', Hash, OccurrenceId),
    hex_bytes(CanonicalHex, Bytes).


occurrence_bytes(Root, Steps, Bytes) :-
    text_utf8_bytes(Root, RootBytes),
    field_bytes(RootBytes, RootField),
    maplist(step_bytes, Steps, StepFields),
    string_codes("LogicLensOccurrence", Header),
    append([Header, [0, 1], RootField|StepFields], Bytes).


step_bytes(step(FactId, Direction), Bytes) :-
    text_utf8_bytes(FactId, FactBytes),
    field_bytes(FactBytes, FactField),
    direction_byte(Direction, DirectionByte),
    append(FactField, [DirectionByte], Bytes).


direction_byte(outgoing, 1).
direction_byte(incoming, 2).


field_bytes(ValueBytes, FieldBytes) :-
    length(ValueBytes, Length),
    uint64_big_endian(Length, LengthBytes),
    append(LengthBytes, ValueBytes, FieldBytes).


uint64_big_endian(Value, Bytes) :-
    Value >= 0,
    Value =< 18446744073709551615,
    Bytes = [B7, B6, B5, B4, B3, B2, B1, B0],
    B7 is (Value >> 56) /\ 255,
    B6 is (Value >> 48) /\ 255,
    B5 is (Value >> 40) /\ 255,
    B4 is (Value >> 32) /\ 255,
    B3 is (Value >> 24) /\ 255,
    B2 is (Value >> 16) /\ 255,
    B1 is (Value >> 8) /\ 255,
    B0 is Value /\ 255.


text_utf8_bytes(Text, Bytes) :-
    (   atom(Text)
    ->  atom_codes(Text, Codes)
    ;   string(Text)
    ->  string_codes(Text, Codes)
    ;   throw(error(type_error(text, Text), occurrence_identity/4))
    ),
    phrase(utf8_codes(Codes), Bytes).
