import unittest

from wikitextprocessor import Wtp
from wiktextract.clean import clean_value
from wiktextract.config import WiktionaryConfig
from wiktextract.thesaurus import close_thesaurus_db
from wiktextract.wxr_context import WiktextractContext


class WiktExtractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.wxr = WiktextractContext(Wtp(), WiktionaryConfig())

    def tearDown(self) -> None:
        self.wxr.wtp.close_db_conn()
        close_thesaurus_db(
            self.wxr.thesaurus_db_path, self.wxr.thesaurus_db_conn
        )

    def test_pos(self):
        poses = self.wxr.config.POS_TYPES
        self.assertTrue(isinstance(poses, set))
        for pos_type in ["noun", "verb", "pron", "adj", "adv", "num"]:
            self.assertIn(pos_type, poses)
        self.assertLess(len(poses), 50)

    def test_cv_plain(self):
        v = "This is a test."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_comment(self):
        v = "This <!--comment--> is a test."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_unk1(self):
        # We no longer clean unknown templates
        v = "This is a {{unknown-asdxfa}} test."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a {{unknown-asdxfa}} test.")

    def test_cv_unk(self):
        # We no longer clean unknown template arguments
        v = "This is a {{{1}}} test."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a {{{1}}} test.")

    def test_cv_ref(self):
        v = "This <ref>junk\nmore junk</ref> is a test."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_html(self):
        v = "This <thispurportstobeatag> is a test."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_html2(self):
        v = "This </thispurportstobeatag> is a test."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_link1(self):
        v = "This is a [[test]]."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_link2(self):
        v = "This is a [[w:foo|test]]."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_link3(self):
        v = "This is a [[w:foo|]]."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a foo.")

    def test_cv_link4(self):
        v = "This is a [[bar]]."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a bar.")

    def test_cv_link5(self):
        v = "([[w:Jurchen script|Jurchen script]]: , Image: [[FIle:Da (Jurchen script).png|25px]])"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "(Jurchen script: , Image: )")

    def test_cv_link6(self):
        v = "[[:w:Foo|Foo]]"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "Foo")

    def test_cv_link7(self):
        v = "[[:w:Foo|Foo [...]]]"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "Foo …")

    def test_cv_link8(self):
        v = "[[File:MiG-17F Top View.JPG|thumb|right|A MiG-17 jet.]]\nBorrowed"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "Borrowed")

    def test_cv_url1(self):
        v = "This is a [http://ylonen.org test]."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_url2(self):
        v = "This is a [http://ylonen.org test1 test2]."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test1 test2.")

    def test_cv_url3(self):
        v = "foo^([http://ylonen.org])"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "foo")

    def test_cv_url4(self):
        v = "foo^(http://ylonen.org)"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "foo")

    def test_cv_url5(self):
        v = "foo [http://ylonen.org]"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "foo http://ylonen.org")

    def test_cv_url6(self):
        v = "[[http://ylonen.org] FOO]"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "FOO")

    def test_cv_q2(self):
        v = "This is a ''test''."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_q3(self):
        v = "This is a '''test'''."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_nbsp(self):
        v = "This is a&nbsp;test."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a test.")

    def test_cv_gt(self):
        v = "This is a &lt;test&gt;."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a <test>.")

    def test_cv_unicode_apostrophe(self):
        v = "This is a t\u2019est."
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This is a t\u2019est.")

    def test_cv_sp(self):
        v = "  This\nis \na\n   test.\t"
        v = clean_value(self.wxr, v)
        # The code has been changed to keep newlines
        self.assertEqual(v, "This\nis\na\n test.")

    def test_cv_presp(self):
        v = " This : is a test . "
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This : is a test .")

    def test_cv_presp2(self):
        v = " This ; is a test , "
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "This ; is a test ,")

    def test_cv_excl(self):
        v = " Run !\n"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "Run !")

    def test_cv_ques(self):
        v = " Run ?\n"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "Run ?")

    def test_cv_math1(self):
        v = r"foo <math>a \times \zeta = c</math> bar"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "foo a×ζ=c bar")

    def test_cv_math2(self):
        v = r"<math>\frac{a}{b + c}</math>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "a/(b+c)")

    def test_cv_math3(self):
        v = r"<math>\frac{a + 1}{b + c}</math>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "(a+1)/(b+c)")

    def test_cv_math4(self):
        v = r"<math>\frac\alpha\beta</math>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "α/β")

    def test_cv_math5(self):
        v = r"<math>{\mathfrak A} - {\mathbb B} \cup {\mathcal K}</math>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "𝔄-𝔹∪𝒦")

    def test_cv_math6(self):
        v = r"<math>\sum_{i=0}^100 1/i</math>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "∑ᵢ₌₀¹⁰⁰1/i")

    def test_cv_math7(self):
        v = r"<math>x^\infty</math>"
        v = clean_value(self.wxr, v)
        print(ascii(v))
        self.assertEqual(v, "x\u2002᪲")

    def test_cv_math8(self):
        v = r"<math>4 7</math>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "4 7")

    def test_cv_math9(self):
        v = r"<math>a x + b</math>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "ax+b")

    def test_cv_math10(self):
        v = r"<math>4^7</math>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "4⁷")

    def test_cv_sup1(self):
        v = r"x<sup>3</sup>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "x³")

    def test_cv_sub1(self):
        v = r"x<sub>3</sub>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "x₃")

    def test_cv_chem1(self):
        v = r"<chem>H2O</chem>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "H₂O")

    def test_cv_ellipsis(self):
        v = "[...]"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "…")

    def test_cv_div1(self):
        v = "foo<div>bar</div>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "foo\nbar")

    def test_cv_paragraph1(self):
        v = "foo\n\nbar"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "foo\nbar")

    def test_cv_html_sp1(self):
        v = "<span>foo</span><span> bar</span>"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "foo bar")

    def test_cv_misc1(self):
        v = """<span style="font-style: normal;">[</span></span><span title="from Their First Rise and Settlement in the Island of Providence, to the Present Time. With the Remarkable Actions and Adventures of the Two Female Pyrates Mary Read and Anne Bonny; [...] To which is Added. A Short Abstract of the Statute and Civil Law, in Relation to Pyracy">  …\n      \n  </span><span class="q-hellip-b"><span style="font-style: normal;">]</span>"""
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "[…]")

    def test_ltr(self):
        v = "a\u200eb"
        v = clean_value(self.wxr, v)
        self.assertEqual(v, "ab")

    def test_second_ref_tag(self) -> None:
        self.assertEqual(
            clean_value(
                self.wxr,
                'some text<ref name="OED"/> some other text<ref>ref text</ref>'
            ),
            "some text some other text"
        )

    def test_bold_node_in_link(self):
        from wiktextract.page import clean_node

        # https://en.wiktionary.org/wiki/ちゃんねる
        # GitHub issue: tatuylonen/wikitextprocessor#170
        wikitext = "{{ja-usex|[[w:ja:2ちゃんねる|2'''ちゃんねる''']]}}"
        self.wxr.wtp.add_page(
            "Template:ja-usex", 10, "{{#invoke:ja-usex|show}}"
        )
        self.wxr.wtp.add_page(
            "Module:ja-usex",
            828,
            """
            local export = {}

            function export.show(frame)
              local first_arg = frame:getParent().args[1]
              if first_arg == "[[w:ja:2ちゃんねる|2'''ちゃんねる''']]" then
                -- bold wikitext shouldn't be removed
                return first_arg .. ", ''italic''"
              end
              return "failed"
            end

            return export
            """
        )
        self.wxr.wtp.start_page("")
        tree = self.wxr.wtp.parse(wikitext)
        # bold and italic nodes should be converted to plain text
        self.assertEqual(
            clean_node(self.wxr, None, tree.children), "2ちゃんねる, italic"
        )
