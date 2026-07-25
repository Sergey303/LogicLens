:- use_module(library(http/json)).
:- use_module(knowledge).
:- initialization(main, main).

main(Argv) :-
    catch(dispatch(Argv, Result), Error, error_result(Error, Result)),
    json_write_dict(current_output, Result, [width(0)]),
    nl.

dispatch(['current-material', Revision, DateAtom], Result) :-
    atom_number(DateAtom, Date),
    findall(
        Solution,
        material_solution(Revision, Date, Solution),
        Solutions
    ),
    material_result(Revision, Date, Solutions, Result).

dispatch([expand, Entity, Kind], Result) :-
    (   expansion(Entity, Kind, Ref, Summary),
        expansion_payload(Ref, Payload)
    ->  Result = _{
            status:"success",
            entity:Entity,
            kind:Kind,
            ref:Ref,
            summary:Summary,
            payload:Payload
        }
    ;   Result = _{
            status:"unknown",
            entity:Entity,
            kind:Kind
        }
    ).

dispatch(_, _{
    status:"invalid_request",
    usage:[
        "current-material <revision> <yyyymmdd>",
        "expand <entity> <kind>"
    ]
}).

material_solution(Revision, Date, Solution) :-
    current_material(Revision, Date, Material, Proof),
    findall(
        _{kind:Kind, ref:Ref, summary:Summary},
        expansion(Material, Kind, Ref, Summary),
        Expansions
    ),
    Solution = _{
        material:Material,
        proof:Proof,
        available_expansions:Expansions
    }.

material_result(Revision, Date, [], _{
    status:"unknown",
    query:_{revision:Revision, date:Date},
    solutions:[]
}).

material_result(Revision, Date, Solutions, _{
    status:"success",
    query:_{revision:Revision, date:Date},
    solutions:Solutions
}) :-
    Solutions \= [].

error_result(Error, _{
    status:"error",
    message:Message
}) :-
    message_to_string(Error, Message).
