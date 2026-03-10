"""
==============================================
公共格式化工具函数单元测试
==============================================
"""

import pytest
from decimal import Decimal
from backend.src.utils.response import (
    success_response,
    error_response,
    paginated_response,
    created_response,
    updated_response,
    deleted_response,
    not_found_response,
    unauthorized_response,
    forbidden_response,
    validation_error_response,
    server_error_response,
)
from backend.src.utils.symbol_utils import (
    format_symbol,
    clean_symbol,
    detect_market,
    parse_symbol,
    is_valid_symbol,
    get_market_name,
    normalize_symbols,
)


class TestResponseFormatters:
    """API 响应格式化工具测试"""

    def test_success_response(self):
        """测试成功响应"""
        result = success_response(data={"id": 1}, message="操作成功")
        assert result["success"] is True
        assert result["data"]["id"] == 1
        assert result["message"] == "操作成功"
        assert result["code"] == 200

    def test_success_response_default_values(self):
        """测试成功响应默认值"""
        result = success_response()
        assert result["success"] is True
        assert result["data"] is None
        assert result["message"] == "操作成功"
        assert result["code"] == 200

    def test_error_response(self):
        """测试错误响应"""
        result = error_response(message="操作失败", code=400)
        assert result["success"] is False
        assert result["message"] == "操作失败"
        assert result["code"] == 400

    def test_paginated_response(self):
        """测试分页响应"""
        data = [{"id": 1}, {"id": 2}]
        result = paginated_response(data=data, total=100, page=2, page_size=10)
        assert result["success"] is True
        assert len(result["data"]) == 2
        assert result["total"] == 100
        assert result["page"] == 2
        assert result["page_size"] == 10
        assert result["total_pages"] == 10

    def test_paginated_response_empty(self):
        """测试空分页响应"""
        result = paginated_response(data=[], total=0)
        assert result["success"] is True
        assert result["data"] == []
        assert result["total_pages"] == 0

    def test_created_response(self):
        """测试创建成功响应"""
        result = created_response(data={"id": 1})
        assert result["success"] is True
        assert result["code"] == 201
        assert result["message"] == "创建成功"

    def test_updated_response(self):
        """测试更新成功响应"""
        result = updated_response(data={"id": 1})
        assert result["success"] is True
        assert result["code"] == 200
        assert result["message"] == "更新成功"

    def test_deleted_response(self):
        """测试删除成功响应"""
        result = deleted_response()
        assert result["success"] is True
        assert result["code"] == 200
        assert result["message"] == "删除成功"

    def test_not_found_response(self):
        """测试资源不存在响应"""
        result = not_found_response()
        assert result["success"] is False
        assert result["code"] == 404

    def test_unauthorized_response(self):
        """测试未授权响应"""
        result = unauthorized_response()
        assert result["success"] is False
        assert result["code"] == 401

    def test_forbidden_response(self):
        """测试禁止访问响应"""
        result = forbidden_response()
        assert result["success"] is False
        assert result["code"] == 403

    def test_validation_error_response(self):
        """测试数据验证失败响应"""
        errors = {"field": "name", "message": "不能为空"}
        result = validation_error_response(errors=errors)
        assert result["success"] is False
        assert result["code"] == 422
        assert result["data"] == errors

    def test_server_error_response(self):
        """测试服务器错误响应"""
        result = server_error_response()
        assert result["success"] is False
        assert result["code"] == 500


class TestSymbolFormatters:
    """股票代码格式化工具测试"""

    def test_format_symbol_auto_detect_shse(self):
        """测试自动检测上海市场"""
        result = format_symbol("600000")
        assert result == "600000.SH"

    def test_format_symbol_auto_detect_szse(self):
        """测试自动检测深圳市场"""
        result = format_symbol("000001")
        assert result == "000001.SZ"

    def test_format_symbol_with_suffix(self):
        """测试带后缀的代码"""
        result = format_symbol("600000.SH")
        assert result == "600000.SH"

    def test_format_symbol_short_code(self):
        """测试短代码补齐"""
        result = format_symbol("1")
        assert result == "000001.SZ"

    def test_clean_symbol(self):
        """测试清理股票代码"""
        assert clean_symbol("600000.SH") == "600000"
        assert clean_symbol("000001.SZ") == "000001"
        assert clean_symbol("600000") == "600000"

    def test_clean_symbol_short_code(self):
        """测试短代码补齐"""
        assert clean_symbol("1") == "000001"

    def test_detect_market_shse(self):
        """测试检测上海市场"""
        assert detect_market("600000") == "SHSE"
        assert detect_market("601318") == "SHSE"

    def test_detect_market_szse(self):
        """测试检测深圳市场"""
        assert detect_market("000001") == "SZSE"
        assert detect_market("300750") == "SZSE"

    def test_detect_market_unknown(self):
        """测试未知市场"""
        assert detect_market("999999") == "UNKNOWN"

    def test_parse_symbol(self):
        """测试解析股票代码"""
        code, market = parse_symbol("600000.SH")
        assert code == "600000"
        assert market == "SHSE"

    def test_is_valid_symbol_valid(self):
        """测试有效股票代码"""
        assert is_valid_symbol("600000") is True
        assert is_valid_symbol("000001") is True
        assert is_valid_symbol("300750") is True

    def test_is_valid_symbol_invalid(self):
        """测试无效股票代码"""
        assert is_valid_symbol("123") is False  # 不是6位
        assert is_valid_symbol("999999") is False  # 无效开头
        assert is_valid_symbol("123456") is False  # 无效开头

    def test_get_market_name_zh(self):
        """测试获取市场中文名称"""
        assert get_market_name("SHSE") == "上海证券交易所"
        assert get_market_name("SZSE") == "深圳证券交易所"

    def test_get_market_name_en(self):
        """测试获取英文名称"""
        assert get_market_name("SHSE", lang="en") == "Shanghai Stock Exchange"
        assert get_market_name("SZSE", lang="en") == "Shenzhen Stock Exchange"

    def test_normalize_symbols(self):
        """测试批量标准化"""
        symbols = ["600000", "000001", "invalid", "300750"]
        result = normalize_symbols(symbols)
        assert len(result) == 3
        assert "600000.SH" in result
        assert "000001.SZ" in result
        assert "300750.SZ" in result
