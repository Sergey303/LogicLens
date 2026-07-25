:- module(epoch_state, [
    loaded_epoch/1,
    loaded_revision/1,
    manifest_summary/1
]).

:- use_module(library(http/json)).


loaded_epoch(0).
loaded_revision(0).


manifest_summary(Summary) :-
    module_property(epoch_state, file(ModuleFile)),
    file_directory_name(ModuleFile, RulesDirectory),
    directory_file_path(RulesDirectory, '../manifest.json', DataManifestRelative),
    directory_file_path(
        RulesDirectory,
        '../ontology/manifest.json',
        OntologyManifestRelative
    ),
    absolute_file_name(DataManifestRelative, DataManifestPath),
    absolute_file_name(OntologyManifestRelative, OntologyManifestPath),
    read_json_file(DataManifestPath, DataManifest),
    read_json_file(OntologyManifestPath, OntologyManifest),
    Summary = _{
        dataHash: DataManifest.dataHash,
        ontologyHash: OntologyManifest.packageHash,
        dataCompilerCommit: DataManifest.compilerCommit,
        ontologyCompilerCommit: OntologyManifest.compilerCommit
    }.


read_json_file(Path, Dict) :-
    setup_call_cleanup(
        open(Path, read, Stream, [encoding(utf8)]),
        json_read_dict(Stream, Dict),
        close(Stream)
    ).
