#!/usr/bin/env python
# -*-encoding:UTF-8-*-

from django import forms

from options.options import SysOptions
from myutils.api import UsernameSerializer, serializers
from myutils.constants import Difficulty
from myutils.serializers import LanguageNameMultiChoiceField, SPJLanguageNameChoiceField, LanguageNameChoiceField

from .models import Problem, ProblemRuleType, ProblemTag
from .utils import parse_problem_template


class TestCaseUploadForm(forms.Form):
    # 测试样例上传表格
    spj = forms.CharField(max_length=12)
    file = forms.FileField()


class CreateSampleSerializer(serializers.Serializer):
    # 创建样例，使用来对一个问题创建例子代码，例如A+B问题
    input = serializers.CharField(trim_whitespace=False)
    output = serializers.CharField(trim_whitespace=False)


class CreateTestCaseScoreSerializer(serializers.Serializer):
    # 创建测试样例分数
    input_name = serializers.CharField(max_length=32)
    output_name = serializers.CharField(max_length=32)
    score = serializers.IntegerField(min_value=0)


class CreateProblemCodeTemplateSerializer(serializers.Serializer):
    pass


class CreateOrEditProblemSerializer(serializers.Serializer):
    # 创建或者编辑问题，此类可以作为基类
    _id = serializers.CharField(max_length=32, allow_blank=True, allow_null=True)
    title = serializers.CharField(max_length=1024)
    description = serializers.CharField()
    input_description = serializers.CharField()
    output_description = serializers.CharField()
    samples = serializers.ListField(child=CreateSampleSerializer(), allow_empty=False)
    test_case_id = serializers.CharField(max_length=32)
    test_case_score = serializers.ListField(child=CreateTestCaseScoreSerializer(), allow_empty=True)
    time_limit = serializers.IntegerField(min_value=1, max_value=1000 * 60)
    memory_limit = serializers.IntegerField(min_value=1, max_value=1024)
    languages = LanguageNameMultiChoiceField()
    template = serializers.DictField(child=serializers.CharField(min_length=1))
    rule_type = serializers.ChoiceField(choices=[ProblemRuleType.ACM, ProblemRuleType.OI])
    spj = serializers.BooleanField()
    spj_language = SPJLanguageNameChoiceField(allow_blank=True, allow_null=True)
    spj_code = serializers.CharField(allow_blank=True, allow_null=True)
    spj_compile_ok = serializers.BooleanField(default=False)
    visible = serializers.BooleanField()
    difficulty = serializers.ChoiceField(choices=Difficulty.choices())
    tags = serializers.ListField(child=serializers.CharField(max_length=32), allow_empty=False)
    hint = serializers.CharField(allow_blank=True, allow_null=True)
    source = serializers.CharField(max_length=256, allow_blank=True, allow_null=True)


class CreateProblemSerializer(CreateOrEditProblemSerializer):
    # 创建问题
    pass


class EditProblemSerializer(CreateOrEditProblemSerializer):
    # 编辑问题，需要使用一个ID来识别
    id = serializers.IntegerField()


class CreateContestProblemSerializer(CreateOrEditProblemSerializer):
    # 创建比赛问题序列化器，需要一个contest_id识别
    contest_id = serializers.IntegerField()


class EditContestProblemSerializer(CreateOrEditProblemSerializer):
    # 编辑比赛问题，需要一个用户id和contest_id来识别
    id = serializers.IntegerField()
    contest_id = serializers.IntegerField()


class TagSerializer(serializers.ModelSerializer):
    # 题目标签序列化器，返回题目的标签序列化数据
    class Meta:
        model = ProblemTag
        fields = "__all__"


class CompileSPJSerializer(serializers.Serializer):
    # 编译特殊评判序列化器
    spj_language = SPJLanguageNameChoiceField()
    spj_code = serializers.CharField()


class BaseProblemSerializer(serializers.ModelSerializer):
    # 基础问题序列化器，包含问题标签类型，和创建的作者
    tags = serializers.SlugRelatedField(many=True, slug_field="name", read_only=True)
    created_by = UsernameSerializer()

    def get_public_template(self, obj):
        # 获取公共的模板
        ret = {}
        for lang, code in obj.template.items():
            ret[lang] = parse_problem_template(code)["template"]
        return ret


class ProblemAdminSerializer(BaseProblemSerializer):
    # 管理管理员继承BaseProblemSerializer，管理问题
    class Meta:
        model = Problem
        fields = "__all__"


class ProblemSerializer(BaseProblemSerializer):
    # 问题序列化器
    template = serializers.SerializerMethodField("get_public_template")

    class Meta:
        model = Problem
        exclude = ("test_case_score", "test_case_id", "visible", "is_public",
                   "spj_code", "spj_version", "spj_compile_ok")


class ProblemSafeSerializer(BaseProblemSerializer):
    # 问题安全序列化器
    template = serializers.SerializerMethodField("get_public_template")

    class Meta:
        model = Problem
        exclude = ("test_case_score", "test_case_id", "visible", "is_public",
                   "spj_code", "spj_version", "spj_compile_ok",
                   "difficulty", "submission_number", "accepted_number", "statistic_info")


class ContestProblemMakePublicSerializer(serializers.Serializer):
    # 将比赛问题公开序列话器，id和display_id作为标识
    id = serializers.IntegerField()
    display_id = serializers.CharField(max_length=32)


class ExportProblemSerializer(serializers.ModelSerializer):
    # 导出问题：id、描述、输入输出描述、测试样例分数、提示、特殊评判、通过模板、来源、标签
    display_id = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    input_description = serializers.SerializerMethodField()
    output_description = serializers.SerializerMethodField()
    test_case_score = serializers.SerializerMethodField()
    hint = serializers.SerializerMethodField()
    spj = serializers.SerializerMethodField()
    template = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    tags = serializers.SlugRelatedField(many=True, slug_field="name", read_only=True)

    def get_display_id(self, obj):
        # 获得显示id
        return obj._id

    def _html_format_value(self, value):
        # HTML格式的值
        return {"format": "html", "value": value}

    def get_description(self, obj):
        # 获得描述
        return self._html_format_value(obj.description)

    def get_input_description(self, obj):
        # 获得输入描述
        return self._html_format_value(obj.input_description)

    def get_output_description(self, obj):
        # 获取输出描述
        return self._html_format_value(obj.output_description)

    def get_hint(self, obj):
        # 获取提示信息
        return self._html_format_value(obj.hint)

    def get_test_case_score(self, obj):
        # 获取测试样例分数
        return [{"score": item["score"] if obj.rule_type == ProblemRuleType.OI else 100,
                 "input_name": item["input_name"], "output_name": item["output_name"]}
                for item in obj.test_case_score]

    def get_spj(self, obj):
        # 获取特殊评判的测试
        return {"code": obj.spj_code,
                "language": obj.spj_language} if obj.spj else None

    def get_template(self, obj):
        # 获取模板
        ret = {}
        for k, v in obj.template.items():
            ret[k] = parse_problem_template(v)
        return ret

    def get_source(self, obj):
        # 获取问题来源
        return obj.source or f"{SysOptions.website_name} {SysOptions.website_base_url}"

    class Meta:
        model = Problem
        fields = ("display_id", "title", "description", "tags",
                  "input_description", "output_description",
                  "test_case_score", "hint", "time_limit", "memory_limit", "samples",
                  "template", "spj", "rule_type", "source", "template")


class AddContestProblemSerializer(serializers.Serializer):
    # 添加比赛问题的序列化：比赛id、问题id、是否公开
    contest_id = serializers.IntegerField()
    problem_id = serializers.IntegerField()
    display_id = serializers.CharField()


class ExportProblemRequestSerialzier(serializers.Serializer):
    # 导出请求问题序列化
    problem_id = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class UploadProblemForm(forms.Form):
    # 上传问题表格
    file = forms.FileField()


class FormatValueSerializer(serializers.Serializer):
    # 格式化值序列化，为HTML或者markdown二选一，值允许为空
    format = serializers.ChoiceField(choices=["html", "markdown"])
    value = serializers.CharField(allow_blank=True)


class TestCaseScoreSerializer(serializers.Serializer):
    # 测试样例总分序列化：分数，输入名称1.in，输出名称1.out
    score = serializers.IntegerField(min_value=1)
    input_name = serializers.CharField(max_length=32)
    output_name = serializers.CharField(max_length=32)


class TemplateSerializer(serializers.Serializer):
    # 模板序列化器,测试通过的示例代码模板
    prepend = serializers.CharField()
    template = serializers.CharField()
    append = serializers.CharField()


class SPJSerializer(serializers.Serializer):
    # 特殊评判序列化器，源代码，语言
    code = serializers.CharField()
    language = SPJLanguageNameChoiceField()


class AnswerSerializer(serializers.Serializer):
    # 答案序列化器，源代码，语言
    code = serializers.CharField()
    language = LanguageNameChoiceField()


class ImportProblemSerializer(serializers.Serializer):
    # 导入问题的序列化器：id、标题、描述、输入输出描述、提示、测试样例分数、
    # 时间限制、内存限制、例子、模板、特殊评判要求、规则类型、来源、答案、标签
    display_id = serializers.CharField(max_length=128)
    title = serializers.CharField(max_length=128)
    description = FormatValueSerializer()
    input_description = FormatValueSerializer()
    output_description = FormatValueSerializer()
    hint = FormatValueSerializer()
    test_case_score = serializers.ListField(child=TestCaseScoreSerializer(), allow_null=True)
    time_limit = serializers.IntegerField(min_value=1, max_value=60000)
    memory_limit = serializers.IntegerField(min_value=1, max_value=10240)
    samples = serializers.ListField(child=CreateSampleSerializer())
    template = serializers.DictField(child=TemplateSerializer())
    spj = SPJSerializer(allow_null=True)
    rule_type = serializers.ChoiceField(choices=ProblemRuleType.choices())
    source = serializers.CharField(max_length=200, allow_blank=True, allow_null=True)
    answers = serializers.ListField(child=AnswerSerializer())
    tags = serializers.ListField(child=serializers.CharField())


class FPSProblemSerializer(serializers.Serializer):
    # 上传文件的序列化器：标题、描述、输入输出、提示、时间限制、内存限制、例子、问题来源、特殊评判、模板（头尾和附加）
    class UnitSerializer(serializers.Serializer):
        unit = serializers.ChoiceField(choices=["MB", "s", "ms"])
        value = serializers.IntegerField(min_value=1, max_value=60000)

    title = serializers.CharField(max_length=128)
    description = serializers.CharField()
    input = serializers.CharField()
    output = serializers.CharField()
    hint = serializers.CharField(allow_blank=True, allow_null=True)
    time_limit = UnitSerializer()
    memory_limit = UnitSerializer()
    samples = serializers.ListField(child=CreateSampleSerializer())
    source = serializers.CharField(max_length=200, allow_blank=True, allow_null=True)
    spj = SPJSerializer(allow_null=True)
    template = serializers.ListField(child=serializers.DictField(), allow_empty=True, allow_null=True)
    append = serializers.ListField(child=serializers.DictField(), allow_empty=True, allow_null=True)
    prepend = serializers.ListField(child=serializers.DictField(), allow_empty=True, allow_null=True)
