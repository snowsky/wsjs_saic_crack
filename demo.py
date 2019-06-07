# coding: utf-8
import hashlib
from pprint import pprint
from urllib import parse

import execjs.runtime_names
import requests
from lxml.etree import HTML

with open("crack.js", encoding="utf-8") as f:
    ctx = execjs.get(execjs.runtime_names.Node).compile(f.read())


class Demo(object):
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Host": "wsjs.saic.gov.cn",
            "Origin": "http://wsjs.saic.gov.cn",
            "Referer": "http://wsjs.saic.gov.cn",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
            # "X-Requested-With": "XMLHttpRequest",
        })

    @staticmethod
    def _get_md5(data: dict) -> str:
        """用于列表页的md5加密"""
        salt = "MR2W3O4M5R3O1P7W3E9M0R6N8H"
        keys = ("request:nc", "request:ncs", "request:mn", "request:sn", "request:hnc", "request:hne", "request:imf")
        values = [parse.quote(data.get(key) or "@", safe="@") for key in keys] + [salt]
        message = "-".join(values)
        digest = hashlib.md5(message.encode()).hexdigest()
        return digest

    def _request_detail(self, url: str, tid: str) -> requests.Response:
        string = f"request:tid={tid}"

        # 更新cookie
        self.session.cookies.update(ctx.call("get_cookies"))

        # 加密请求参数
        path = parse.urlparse(url).path
        y7b = ctx.call("get_y7bRbp", path, string)
        c1k5 = ctx.call("get_c1K5tw0w6", string, y7b, 2)
        params = {"y7bRbp": y7b, "c1K5tw0w6_": c1k5}

        response = self.session.post(url, params=params)
        if response.status_code != 200:
            print(response.content.decode())
            raise Exception(response.status_code)

        return response

    def list_page(self, keyword):
        """列表页(综合查询)"""

        # 第一阶段，先访问html页面
        url = "http://wsjs.saic.gov.cn/txnRead01.do"

        request_args = {
            "request:queryCom": "1",  # 不明
            "locale": "zh_CN",  # 语言
            "request:nc": "",  # 国际分类
            "request:sn": "",  # 申请/注册号
            "request:mn": keyword,  # 商标名称
            "request:hnc": "",  # 申请人名称(中文)
            "request:hne": "",  # 申请人名称(英文)
            "request:md5": None,  # md5签名
        }
        request_args["request:md5"] = Demo._get_md5(request_args)
        string = "&".join(f"{k}={v}" for k, v in request_args.items())

        # 更新cookie
        self.session.cookies.update(ctx.call("get_cookies"))

        # 加密请求参数
        y7b = ctx.call("get_y7bRbp", parse.urlparse(url).path, "")
        params = {"y7bRbp": y7b}
        c1k5 = ctx.call("get_c1K5tw0w6", string, y7b, 7, True)
        data = {"c1K5tw0w6_": c1k5}

        response = self.session.post(url, params=params, data=data)
        if response.status_code != 200:
            print(response.content.decode())
            raise Exception(response.status_code)

        meta = HTML(response.content).xpath("//*[@id='9DhefwqGPrzGxEp9hPaoag']")[0].get("content")
        html_tags = ctx.call("get_hidden_input", meta)
        html_args = {tag.get("name"): tag.get("value") for tag in HTML(html_tags).xpath("//input")}

        # 第二阶段，请求数据接口
        url2 = "http://wsjs.saic.gov.cn/txnRead02.ajax"
        page = 1
        page_size = 50

        ajax_args = {
            "request:queryCom": "1",
            "locale": "zh_CN",  # 语言
            "request:nc": "",  # 国际分类
            "request:sn": "",  # 申请/注册号
            "request:mn": keyword,  # 商标名称
            "request:hnc": "",  # 申请人名称(中文)
            "request:hne": "",  # 申请人名称(英文)

            "request:imf": "",
            "request:maxHint": "",
            "request:ncs": "",
            "request:queryAuto": "",
            "request:queryExp": f"mnoc = {keyword}*",
            "request:queryMode": "",
            "request:queryType": "",
            "request:mi": html_args["request:mi"],
            "request:tlong": html_args["request:tlong"],

            "attribute-node:record_cache-flag": "false",
            "attribute-node:record_page": page,
            "attribute-node:record_page-row": page_size,
            "attribute-node:record_sort-column": "RELEVANCE",
            "attribute-node:record_start-row": (page - 1) * page_size + 1,
        }
        string = "&".join(f"{k}={parse.quote(str(v))}" for k, v in ajax_args.items())

        # 更新cookie
        self.session.cookies.update(ctx.call("get_cookies"))

        # 加密请求参数
        mm = ctx.call("get_MmEwMD", parse.urlparse(url2).path)
        params = {"MmEwMD": mm}
        c1k5 = ctx.call("get_c1K5tw0w6", string, mm, 5)
        data = {"c1K5tw0w6_": c1k5}

        response = self.session.post(url2, params=params, data=data)

        if response.status_code != 200:
            print(response.content.decode())
            raise Exception(response.status_code)

        for tag in HTML(response.content).xpath("//record"):
            print({
                "tid": tag.xpath("tid/text()")[0],
                "申请/注册号": tag.xpath("tmid/text()")[0],
                "国际分类": tag.xpath("nc/text()")[0],
                "申请日期": tag.xpath("fd/text()")[0],
                "商标名称": tag.xpath("mno/text()")[0],
                "申请人名称": tag.xpath("hnc/text()")[0],
            })

    def detail_page(self, tid):
        """详情页(商标详情页+商标流程页) demo"""

        # 商标详情页
        url = "http://wsjs.saic.gov.cn/txnDetail.do"
        response = self._request_detail(url, tid)
        html = HTML(response.content)

        if not all((not v or v == "null") for v in html.xpath("//*[@id='detailParameter']/input/@value")):
            page_data = {
                "商标图片": html.xpath("//*[@id='tmImage']/@img_src")[0],
                "商品/服务": "".join(html.xpath("//*[@class='info']")[0].text.split()),
                "类似群": [dict(zip(["类似群", "商品名称"], tr.xpath("td/text()"))) for tr in html.xpath("//*[@id='list_box']/table/tr")[1:]],
            }
            for tr in html.xpath("//*[@id='tmContent']/table[2]/tr")[:-1]:
                td_list = tr.xpath("td")
                for index in range(0, len(td_list), 2):
                    key = td_list[index].xpath("span/text()")
                    if key:
                        key = key[0]
                        value = (td_list[index + 1].xpath("text()") or [""])[0]
                        page_data[key] = value.strip()
            pprint(page_data)
        else:
            print("商标详情无数据，可能是商标正等待受理，暂无法查询详细信息。")

        # 商标流程页
        url = "http://wsjs.saic.gov.cn/txnDetail2.do"
        response = self._request_detail(url, tid)
        html = HTML(response.content)

        keys = ("申请/注册号", "业务名称", "环节名称", "结论", "日期")
        for table in html.xpath("//*[@class='lcbg']//table"):
            values = [td.xpath("string()") for td in table.xpath(".//td")]
            print(dict(zip(keys, values)))


if __name__ == "__main__":
    demo = Demo()
    demo.list_page(keyword="华为")
    demo.detail_page(tid="TID199406782BEAD70FCC31BB9CC78F277CB4A2EBA5A09")
