from typing import Dict, List, Union

from wikitextprocessor import NodeKind, WikiNode
from wikitextprocessor.parser import TemplateNode

from wiktextract.page import clean_node
from wiktextract.wxr_context import WiktextractContext


def extract_form_line(
    wxr: WiktextractContext,
    page_data: List[Dict],
    nodes: List[Union[WikiNode, str]],
) -> None:
    """
    Ligne de forme
    https://fr.wiktionary.org/wiki/Wiktionnaire:Structure_des_pages#Syntaxe

    A line of wikitext between pos subtitle and the first gloss, contains IPA,
    gender and inflection forms.
    """
    for node in nodes:
        if isinstance(node, WikiNode) and node.kind == NodeKind.TEMPLATE:
            if node.template_name in {"pron", "prononciation", "//"}:
                page_data[-1]["sounds"].append(
                    {"ipa": clean_node(wxr, None, node)}
                )
            elif node.template_name == "équiv-pour":
                process_equiv_pour_template(node, page_data)
            elif node.template_name.startswith("zh-mot"):
                process_zh_mot_template(wxr, node, page_data)
            else:
                tag = clean_node(wxr, page_data[-1], node)
                page_data[-1]["tags"].append(tag)


def process_equiv_pour_template(
    node: TemplateNode, page_data: List[Dict]
) -> None:
    # equivalent form: https://fr.wiktionary.org/wiki/Modèle:équiv-pour
    form_type = node.template_parameters.get(1)
    for template_arg_index in range(2, 8):
        form = node.template_parameters.get(template_arg_index)
        if form is not None:
            page_data[-1]["forms"].append(
                {"form": form, "tags": [f"pour {form_type}"]}
            )


def process_zh_mot_template(
    wxr: WiktextractContext,
    node: TemplateNode,
    page_data: List[Dict],
) -> None:
    # zh-mot, zh-mot-s, zh-mot-t
    # https://fr.wiktionary.org/wiki/Modèle:zh-mot
    node = wxr.wtp.parse(
        wxr.wtp.node_to_wikitext(node),
        pre_expand=True,
        additional_expand={node.template_name},
    )
    for template_node in node.find_child(NodeKind.TEMPLATE):
        if template_node.template_name == "lang":
            page_data[-1]["sounds"].append(
                {
                    "zh-pron": clean_node(wxr, None, template_node),
                    "tags": ["Pinyin"],
                }
            )
        elif template_node.template_name == "pron":
            page_data[-1]["sounds"].append(
                {"ipa": clean_node(wxr, None, template_node)}
            )