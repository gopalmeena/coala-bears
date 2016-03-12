import unittest
from queue import Queue

from coalib.settings.Setting import Setting
from bears.general.AnnotationBear import AnnotationBear
from coalib.results.SourceRange import SourceRange
from coalib.settings.Section import Section
from tests.LocalBearTestHelper import execute_bear


class AnnotationBearTest(unittest.TestCase):

    def setUp(self):
        self.section = Section("")
        self.section.append(Setting('language', 'c'))
        self.section.append(Setting('language_family', 'c'))

    def assertOnlyComment(self, file, uut):
        with execute_bear(uut,
                          "filename",
                          file) as results:
            for result in results:
                self.assertNotIn("Here are the multi-line strings",
                                 result.message)
                self.assertNotIn("Here are the single-line strings",
                                 result.message)

            self.assertNotEqual(results, [])

    def assertOnlyString(self, file, uut):
        results = uut.execute("filename",  file)
        for result in results:
            self.assertNotIn("Here are the multi-line comments",
                             result.message)
            self.assertNotIn("Here are the single-line comments",
                             result.message)

        self.assertNotEqual(results, [])

    def assertRange(self, file, uut, sourcerange):
        results = uut.execute("filename", file)
        for result in results:
            for code in result.affected_code:
                self.assertEqual(code.start.line, sourcerange.start.line)
                self.assertEqual(code.start.column, sourcerange.start.column)
                self.assertEqual(code.end.line, sourcerange.end.line)
                self.assertEqual(code.end.column, sourcerange.end.column)
        self.assertNotEqual(results, [])

    def test_comments(self):
        file = """comments\n/*in line2*/,  \n"""
        uut = AnnotationBear(self.section, Queue())

        self.assertOnlyComment(file, uut)

        file = """comments \n/*"then a string in comment"*/"""
        self.assertOnlyComment(file, uut)

        file = """ this line has a //comment """
        self.assertOnlyComment(file, uut)

        file = """ i have a comment /* and a //comment inside a comment*/ """
        sourcerange = SourceRange.from_values("filename", 1, 19, 1, 56)
        self.assertRange(file, uut, sourcerange)

        file = """ i have a comment /* and a /*comment inside*/ a comment*/ """
        sourcerange = SourceRange.from_values("filename", 1, 19, 1, 46)
        self.assertRange(file, uut, sourcerange)

    def test_string(self):
        section = Section("")
        section.append(Setting('language', 'python3'))
        section.append(Setting('language_family', 'python3'))
        uut = AnnotationBear(section, Queue())
        file = """ strings: "only string" """
        self.assertOnlyString(file, uut)

        file = """ strings: " #then a comment in string" """
        self.assertOnlyString(file, uut)

        file = ' """Trying a multinline string""" '
        self.assertOnlyString(file, uut)

        file = """ i have a string: " and a #comment inside a string" """
        sourcerange = SourceRange.from_values("filename", 1, 19, 1, 52)
        self.assertRange(file, uut, sourcerange)

        file = """ i have a string: " and a 'string' inside a string" """
        sourcerange = SourceRange.from_values("filename", 1, 19, 1, 52)
        self.assertRange(file, uut, sourcerange)
