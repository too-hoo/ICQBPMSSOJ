#!/usr/bin/env python
# -*-encoding:UTF-8-*-

import re

# 基础模板
TEMPLATE_BASE = """//PREPEND BEGIN
{}
//PREPEND END

//TEMPLATE BEGIN
{}
//TEMPLATE END

//APPEND BEGIN
{}
//APPEND END"""


# 解析问题模板
def parse_problem_template(template_str):
    prepend = re.findall(r"//PREPEND BEGIN\n([\s\S]+?)//PREPEND END", template_str)
    template = re.findall(r"//TEMPLATE BEGIN\n([\s\S]+?)//TEMPLATE END", template_str)
    append = re.findall(r"//APPEND BEGIN\n([\s\S]+?)//APPEND END", template_str)
    return {"prepend": prepend[0] if prepend else "",
            "template": template[0] if template else "",
            "append": append[0] if append else ""}


# 传入参数，填充到TEMPLATE_BASE里面去
def build_problem_template(prepend, template, append):
    return TEMPLATE_BASE.format(prepend, template, append)
