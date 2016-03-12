from coalib.parsing.StringProcessing.Core import (unescaped_search_for,
                                                  search_for,
                                                  search_in_between,
                                                  unescaped_search_in_between)
from coalib.bearlib.languages.LanguageDefinition import LanguageDefinition
from coalib.results.SourceRange import SourceRange
from coalib.bears.LocalBear import LocalBear
from coalib.results.RESULT_SEVERITY import RESULT_SEVERITY
from coalib.results.Result import Result


class AnnotationBear(LocalBear):

    def run(self, filename, file: str, language: str, language_family: str):
        """
        Finds out all the positions of comments and strings.
        """
        file = ''.join(file)
        annot_dict = {}
        annot_dict['comment'] = {}
        annot_dict['string'] = {}
        annot_dict['string']["multiline"] = {}
        annot_dict['string']["singleline"] = {}
        annot_dict['comment']["singleline"] = {}
        annot_dict['comment']["multiline"] = {}
        # Tuple of tuples containing start and end of annotations
        match_pos = ()
        lang_dict = LanguageDefinition(language, language_family)

        annot_dict['comment']["singleline"].update(
                    lang_dict["comment_delimiter"])

        annot_dict['comment']["multiline"].update(
                    lang_dict["multiline_comment_delimiters"])

        annot_dict['string']["singleline"].update(
                    lang_dict["string_delimiters"])

        annot_dict['string']["multiline"].update(
                    lang_dict["multiline_string_delimiters"])

        multi_str = single_str = multi_comm = ()
        search_dict = annot_dict['string']['multiline']
        multi_str = find_string_comment(file, search_dict, True)
        search_dict = annot_dict['string']['singleline']
        single_str = find_string_comment(file, search_dict, True)
        search_dict = annot_dict['comment']["multiline"]
        multi_comm = find_string_comment(file, search_dict, False)

        match_pos += multi_str + multi_comm + single_str
        print(match_pos)
        match_pos = remove_nested(match_pos)

        # since single-line comments don't have a definite start and end
        single_comm = []
        for comment_type in annot_dict['comment']["singleline"]:
            for i in search_for(comment_type, file):
                if not in_range_list(match_pos, (i.start(), i.end())):
                    end = file.find('\n', i.start())
                    if end != -1:
                        single_comm.append((i.start(), end))
                    else:
                        file = file + '\n'
                        end = file.find('\n', i.start())
                        single_comm.append((i.start(), end))
        # tuple since its immutable
        single_comm = tuple(single_comm)
        match_pos += single_comm
        match_pos = remove_nested(match_pos)
        print(match_pos)
        affected_code = list(get_range(file, filename, match_pos, multi_comm))
        if affected_code:
            yield Result(origin=self,
                         message="Here are the multi-line comments ",
                         affected_code=affected_code,
                         severity=RESULT_SEVERITY.INFO)

        affected_code = list(get_range(file, filename, match_pos, single_comm))
        if affected_code:
            yield Result(origin=self,
                         message="Here are the single-line comments ",
                         affected_code=affected_code,
                         severity=RESULT_SEVERITY.INFO)

        affected_code = list(get_range(file, filename, match_pos, single_str))

        if affected_code:
            yield Result(origin=self,
                         message="Here are single-line strings",
                         affected_code=affected_code,
                         severity=RESULT_SEVERITY.INFO)

        affected_code = list(get_range(file, filename, match_pos, multi_str))
        if affected_code:
            yield Result(origin=self,
                         message="Here are multi-line strings",
                         affected_code=affected_code,
                         severity=RESULT_SEVERITY.INFO)


def get_range(file, filename, match_pos, string_comment):
    """
    Checks if range is valid and then yields it
    """
    search_range = []
    for i in string_comment:
        if i in match_pos:
            search_range.append(i)
    search_range = [(calc_line_col(file, start), calc_line_col(file, end))
                    for (start, end) in search_range]

    for i in search_range:
        yield SourceRange.from_values(filename,
                                      start_line=i[0][0],
                                      start_column=i[0][1],
                                      end_line=i[1][0],
                                      end_column=i[1][1])


def find_string_comment(file, annot, escape):
    """
    gives all instances of strings and multiline comments found within
    the file, even if they are nested in other strings or comments
    """
    if escape:
        search_func = unescaped_search_in_between
    else:
        search_func = search_in_between
    found_pos = ()
    for annot_type in annot:
        found_pos += tuple(search_func(annot_type, annot[annot_type], file))
    if found_pos:
        found_pos = tuple((i.begin.range[0], i.end.range[1])
                          for i in found_pos)
    return found_pos


def in_range_list(outside_range_list, inside_range):
    """
    finds if a given 'range' is inside a any of the 'ranges' in
    a list of ranges
    """
    for outside_range in outside_range_list:
        if inside_range == outside_range:
            print("continuing...", outside_range, inside_range)
            continue

        elif inside_range[0] == outside_range[0]:
            if inside_range[1] < outside_range[1]:
                return True

        elif inside_range[0] in range(outside_range[0], outside_range[1]):
            print("found", inside_range, "in ", outside_range)
            return True
    return False


def calc_line_col(file, pos_to_find):
    """
    Calculate line number and column in the file, from position
    """
    line = 1
    pos = -1
    pos_new_line = file.find('\n')
    while True:
        if pos_new_line == -1:
            return (line, pos_to_find-pos)

        if pos_to_find <= pos_new_line:
            return (line, pos_to_find - pos)

        else:
            line += 1
            pos = pos_new_line
            pos_new_line = file.find('\n', pos_new_line + 1)


def remove_nested(match_pos):
    """
    removes all the entries from a listthat are nested
    inside some other entry of that list
    """
    unnested_list = []
    for i in match_pos:
        if not in_range_list(match_pos, i):
            unnested_list.append(i)
        else:
            print("removing", i)
    return tuple(unnested_list)
