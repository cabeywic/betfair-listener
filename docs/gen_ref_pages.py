"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files

import os

nav = mkdocs_gen_files.Nav()


def get_test_from_src(src_path: Path) -> Path:
    """Gets test file from source file

    takes a parameter of code location ie /src/module/main.py
    and updates it so that it points to the test file for that file
    the tests dir mirrors the src dir
    so /src/module/main.py would be updated to /tests/module/test_main.py

    Args:
        src_path: (Path) the path object representing the location of src code

    Returns:
        (Path) : location of the corresponding test file
    """

    generated_test_path = str(src_path).replace("src", "tests")
    generated_test_path_parts = generated_test_path.split("/")
    generated_test_path = "/".join(generated_test_path_parts)
    generated_test_path = Path(generated_test_path)
    generated_test_path = generated_test_path.with_name(
        "test_" + generated_test_path.name
    )
    return generated_test_path


def add_label(path: Path, label: str) -> Path:
    """Add a label to a path

    Takes a path of the form /a/b/c/file.py
    and updates it such that the file name is prefixed with label
    ie if label is xyz
    would return /a/b/c/xyz/file.py

    Args:
        path: (Path) the file path to update
        label: the label to set it to

    Returns:
        (Path) : Path object representing the updated file location
    """

    split_path = str(path).split("/")
    end = split_path[-1]
    everything_else = split_path[:-1]
    first_part = "/".join(everything_else)
    second_part = "/" + label + "/" + end
    return Path(first_part + second_part)


def get_test_paths(src_path: Path):
    """Generate paths for tests

    takes input of source code location, gets location of test and returns it's location
    as well as the location to create the doc

    Args:
        src_path: (Path) location of source code

    Returns:
        Path,Path : location to create doc file, location of test
        None,None : if cant locate test file returns tuple of none
    """
    test_path = None
    test_doc_path = None
    if module_path.name != "__init__":
        module_test_path = get_test_from_src(src_path)
        module_test_path = module_test_path.with_suffix("")

        absolute_path = Path(os.getcwd(),module_test_path)
        absolute_path = absolute_path.with_suffix(".py")
        if(not absolute_path.is_file()):
            return None,None

        test_path = module_test_path
        module_test_doc_path = module_test_path.with_suffix(".md")
        full_module_test_doc_path = Path("reference", module_test_doc_path)

        # remove tests from path, this is to put the tests label in a different place
        full_module_test_doc_path = Path(
            str(full_module_test_doc_path).replace("/tests/", "/")
        )
        full_module_test_doc_path = add_label(full_module_test_doc_path, "tests")
        
        test_doc_path = full_module_test_doc_path
    if isinstance(test_doc_path, Path) and isinstance(test_path, Path):
        return test_doc_path, test_path
    return None, None


def get_module_paths(src_path: Path):
    """Get paths of documentation and module

    Takes in location of source code, returns where to create documentation
    and the location of the module

    Args:
        src_path: The location of the source code
    Returns:
        (Path,Path) : path of where to create module documentation, path of module
    """

    module_path = src_path.with_suffix("")
    module_doc_path = module_path.with_suffix(".md")

    full_module_doc_path = Path("reference", module_doc_path)

    # remove src from path so as to be able to replace it in a different location
    full_module_doc_path = Path(str(full_module_doc_path).replace("/src/", "/"))
    full_module_doc_path = add_label(full_module_doc_path, "code")

    return full_module_doc_path, module_path


def write_doc_file(doc_location: Path, source_location: Path):
    """Writes to doc file

    writes source code location to doc file to be processed by mkdocstrings

    Args:
        doc_location: (Path) the location of the doc file to write
        source_location: (Path) the location of the source code file
    """
    with mkdocs_gen_files.open(doc_location, "w") as doc_file:
        ident = ".".join(tuple(source_location.parts))
        doc_file.write(f"::: {ident}")


for path in sorted(Path("src").rglob("*.py")):

    module_doc_path, module_path = get_module_paths(path)
    test_doc_path, test_path = get_test_paths(path)
    module_path_parts = tuple(module_path.parts)

    if module_path_parts[-1] == "__init__":
        # for some reason we cant import init, this isn't a huge deal as no code is contained, so skip it
        module_path_parts = module_path_parts[:-1]
        module_doc_path = module_doc_path.with_name("index.md")
        parts_labelled = list(module_path_parts)
        continue
    else:
        parts_labelled = list(module_path_parts)
        parts_labelled.insert(len(parts_labelled) - 1, "Code")

    module_doc_path_nav = Path("/".join(str(module_doc_path).split("/")[1:]))

    parts_labelled = tuple(parts_labelled)
    nav[parts_labelled[1:]] = module_doc_path_nav.as_posix()

    write_doc_file(module_doc_path, module_path)

    if test_path is not None and test_doc_path is not None:
        parts_labelled = list(test_path.parts)
        parts_labelled.insert(len(parts_labelled) - 1, "Tests")
        parts_labelled = tuple(parts_labelled)

        test_doc_path_nav = Path("/".join(str(test_doc_path).split("/")[1:]))
        nav[parts_labelled[1:]] = test_doc_path_nav.as_posix()

        write_doc_file(test_doc_path, test_path)

    # i dont know what this does
    mkdocs_gen_files.set_edit_path(module_doc_path, path)


with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
