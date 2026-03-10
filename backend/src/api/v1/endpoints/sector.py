"""
Sector Analysis Endpoint

板块分析相关端点。
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
import logging

from src.services.data.akshare import AkShareDataSource

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/sectors")
async def get_sectors(
    sector_type: str = Query(default="industry", description="板块类型: industry(行业), concept(概念), region(地域)")
):
    """
    获取板块列表

    Args:
        sector_type: 板块类型
            - industry: 行业板块
            - concept: 概念板块
            - region: 地域板块

    Returns:
        板块列表
    """
    try:
        data_source = AkShareDataSource()

        if sector_type == "industry":
            sectors = data_source.get_industry_sectors()
        elif sector_type == "concept":
            sectors = data_source.get_concept_sectors()
        elif sector_type == "region":
            sectors = data_source.get_region_sectors()
        else:
            raise HTTPException(status_code=400, detail=f"不支持的板块类型: {sector_type}")

        return {
            "success": True,
            "data": sectors,
            "meta": {
                "sector_type": sector_type,
                "count": len(sectors)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取板块列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取板块列表失败: {str(e)}")


@router.get("/sectors/{sector_name}")
async def get_sector_detail(
    sector_name: str,
    sector_type: str = Query(default="industry", description="板块类型: industry, concept, region")
):
    """
    获取板块详情和成分股

    Args:
        sector_name: 板块名称
        sector_type: 板块类型

    Returns:
        板块详情及成分股列表
    """
    try:
        data_source = AkShareDataSource()

        # 获取板块成分股
        stocks = data_source.get_sector_stocks(sector_name, sector_type)

        # 获取板块行情统计
        stats = data_source.get_sector_stats(sector_name, sector_type)

        return {
            "success": True,
            "data": {
                "name": sector_name,
                "type": sector_type,
                "stocks": stocks,
                "stats": stats
            }
        }

    except Exception as e:
        logger.error(f"获取板块详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取板块详情失败: {str(e)}")


@router.get("/sectors/stats/overview")
async def get_sectors_stats_overview(
    sector_type: str = Query(default="industry", description="板块类型: industry, concept, region")
):
    """
    获取板块涨跌统计概览

    Args:
        sector_type: 板块类型

    Returns:
        各板块涨跌统计
    """
    try:
        data_source = AkShareDataSource()

        # 获取板块统计
        stats = data_source.get_all_sectors_stats(sector_type)

        # 按涨跌幅排序
        sorted_stats = sorted(stats, key=lambda x: x.get("change_pct", 0), reverse=True)

        # 统计概览
        up_count = len([s for s in sorted_stats if s.get("change_pct", 0) > 0])
        down_count = len([s for s in sorted_stats if s.get("change_pct", 0) < 0])
        flat_count = len(sorted_stats) - up_count - down_count

        return {
            "success": True,
            "data": sorted_stats,
            "summary": {
                "total": len(sorted_stats),
                "up": up_count,
                "down": down_count,
                "flat": flat_count,
                "best": sorted_stats[0] if sorted_stats else None,
                "worst": sorted_stats[-1] if sorted_stats else None
            }
        }

    except Exception as e:
        logger.error(f"获取板块统计概览失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取板块统计概览失败: {str(e)}")
