from typing import Union

from wikitextprocessor import NodeKind, WikiNode
from wikitextprocessor.parser import HTMLNode, TemplateNode
from wiktextract.page import clean_node
from wiktextract.wxr_context import WiktextractContext

from .conjugation import extract_conjugation
from .models import Form, Sound, WordEntry
from .pronunciation import PRON_TEMPLATES, process_pron_template


def extract_form_line(
    wxr: WiktextractContext,
    page_data: list[WordEntry],
    nodes: list[Union[WikiNode, str]],
) -> None:
    """
    Ligne de forme
    https://fr.wiktionary.org/wiki/Wiktionnaire:Structure_des_pages#Syntaxe

    A line of wikitext between pos subtitle and the first gloss, contains IPA,
    gender and inflection forms.
    """
    pre_template_name = ""
    for node in nodes:
        if isinstance(node, WikiNode) and node.kind == NodeKind.TEMPLATE:
            if node.template_name in PRON_TEMPLATES:
                ipa_text = process_pron_template(wxr, node)
                if len(ipa_text) > 0:
                    page_data[-1].sounds.append(Sound(ipa=ipa_text))
            elif node.template_name == "équiv-pour":
                process_equiv_pour_template(wxr, node, page_data)
            elif node.template_name.startswith("zh-mot"):
                process_zh_mot_template(wxr, node, page_data)
            elif node.template_name == "ja-mot":
                process_ja_mot_template(wxr, node, page_data)
            elif node.template_name in (
                "conj",
                "conjugaison",
            ) or node.template_name.startswith(("ja-adj-", "ja-verbe")):
                process_conj_template(wxr, node, page_data)
            else:
                tag = clean_node(wxr, page_data[-1], node)
                if (
                    tag.startswith("(")
                    and tag.endswith(")")
                    and pre_template_name in PRON_TEMPLATES
                    and len(page_data[-1].sounds) > 0
                ):
                    # it's the location of the previous IPA template
                    page_data[-1].sounds[-1].tags.append(tag.strip("()"))
                elif len(tag.strip("()")) > 0:
                    page_data[-1].tags.append(tag.strip("()"))

            pre_template_name = node.template_name
        elif isinstance(node, WikiNode) and node.kind == NodeKind.ITALIC:
            tag = clean_node(wxr, None, node)
            if tag != "ou":
                page_data[-1].tags.append(tag)


def process_equiv_pour_template(
    wxr: WiktextractContext, node: TemplateNode, page_data: list[WordEntry]
) -> None:
    # equivalent form: https://fr.wiktionary.org/wiki/Modèle:équiv-pour
    expanded_node = wxr.wtp.parse(
        wxr.wtp.node_to_wikitext(node), expand_all=True
    )
    form_tag = ""
    for child in expanded_node.find_child(NodeKind.ITALIC | NodeKind.HTML):
        if child.kind == NodeKind.ITALIC:
            form_tag = clean_node(wxr, None, child).strip("() ")
        elif isinstance(child, HTMLNode) and child.tag == "bdi":
            form_data = Form(
                form=clean_node(wxr, None, child),
                source="form line template 'équiv-pour'",
            )
            if len(form_tag) > 0:
                form_data.tags = [form_tag]
            if len(form_data.form) > 0:
                page_data[-1].forms.append(form_data)


def process_zh_mot_template(
    wxr: WiktextractContext,
    node: TemplateNode,
    page_data: list[WordEntry],
) -> None:
    # Chinese form line template: zh-mot, zh-mot-s, zh-mot-t
    # https://fr.wiktionary.org/wiki/Modèle:zh-mot
    node = wxr.wtp.parse(
        wxr.wtp.node_to_wikitext(node),
        pre_expand=True,
        additional_expand={node.template_name},
    )
    for template_node in node.find_child(NodeKind.TEMPLATE):
        if template_node.template_name.lower() == "lang":
            page_data[-1].sounds.append(
                Sound(
                    zh_pron=clean_node(wxr, None, template_node),
                    tags=["Pinyin"],
                )
            )
        elif template_node.template_name in ("pron", "prononciation"):
            page_data[-1].sounds.append(
                Sound(ipa=clean_node(wxr, None, template_node))
            )


def process_ja_mot_template(
    wxr: WiktextractContext,
    template_node: TemplateNode,
    page_data: list[WordEntry],
) -> None:
    # Japanese form line template: https://fr.wiktionary.org/wiki/Modèle:ja-mot
    expanded_node = wxr.wtp.parse(
        wxr.wtp.node_to_wikitext(template_node), expand_all=True
    )
    existing_forms = {
        existing_form.form for existing_form in page_data[-1].forms
    }
    for index, node in expanded_node.find_html("span", with_index=True):
        # the first span tag is the word, the second is Hepburn romanization
        if index == 1:
            form_text = clean_node(wxr, None, node)
            if form_text not in existing_forms:
                # avoid adding duplicated form data extracted from
                # inflection table before the form line
                page_data[-1].forms.append(
                    Form(form=form_text, tags=["romanization"])
                )
            break


def process_conj_template(
    wxr: WiktextractContext,
    template_node: TemplateNode,
    page_data: list[WordEntry],
) -> None:
    # https://fr.wiktionary.org/wiki/Modèle:conjugaison
    expanded_node = wxr.wtp.parse(
        wxr.wtp.node_to_wikitext(template_node), expand_all=True
    )
    for link in expanded_node.find_child(NodeKind.LINK):
        if len(link.largs) == 0:
            continue
        conj_title = link.largs[0][0]
        if not conj_title.startswith("Conjugaison:"):
            continue
        conj_word = conj_title.split("/", 1)[-1]
        if conj_word in (
            "Premier groupe",
            "Deuxième groupe",
            "Troisième groupe",
        ):
            continue
        if (
            len(page_data) > 1
            and page_data[-2].lang_code == page_data[-1].lang_code
            and page_data[-2].pos == page_data[-1].pos
            and len(page_data[-2].forms) > 0
            and page_data[-2].forms[-1].source == conj_title
        ):
            page_data[-1].forms = page_data[-2].forms
        else:
            extract_conjugation(wxr, page_data[-1], conj_title)

    tag = clean_node(wxr, page_data[-1], expanded_node)
    if template_node.template_name in ("conj", "conjugaison"):
        tag = tag.removesuffix("(voir la conjugaison)").strip()
    elif template_node.template_name.startswith("ja-"):
        tag = (
            tag.removesuffix("(conjugaison)").removesuffix("(flexions)").strip()
        )
    if len(tag) > 0:
        page_data[-1].tags.append(tag)
