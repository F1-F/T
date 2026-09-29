import requests
import re
import demjson3 as demjson
import json
import hashlib
import sys
import os


session = requests.Session()

COMMON_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
}

session.headers.update(COMMON_HEADERS)


def read_local_json(file_path):
    """读取本地JSON文件"""

    with open(file_path, "rb") as f:
        raw_content = f.read()

    content = raw_content.decode("utf-8")

    # 删除js注释
    content = re.sub(
        r'^//.*$',
        '',
        content,
        flags=re.MULTILINE
    ).strip()

    return content



def extract_and_save_spider(json_text):
    """
    下载spider
    保存为 jar/aowu.jar
    """

    match = re.search(
        r'"spider"\s*:\s*"([^"]+)"',
        json_text
    )

    if not match:
        raise ValueError("未找到 spider 字段")


    spider_url = match.group(1).split(";")[0]

    print(f"📥 下载 spider: {spider_url}")


    resp = session.get(
        spider_url,
        timeout=30,
        allow_redirects=True
    )

    resp.raise_for_status()


    os.makedirs("../jar", exist_ok=True)


    with open("../jar/aowu.jar", "wb") as f:
        f.write(resp.content)


    print("✅ spider保存: ../jar/aowu.jar")



def get_md5(filepath):

    md5 = hashlib.md5()

    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            md5.update(chunk)

    return md5.hexdigest()



def clean_data(raw_text):

    # 替换AOWU扩展地址

    raw_text = re.sub(
        r'https?://[^/]+/https://raw\.githubusercontent\.com/F1-F/T/[^"]+',
        './AOWU',
        raw_text
    )


    data = demjson.decode(raw_text)


    return data



class CompactJSONEncoder(json.JSONEncoder):

    def iterencode(self, o, _one_shot=False):

        def _compact_list(lst, indent_level):

            pad = '  ' * indent_level

            if all(isinstance(i, dict) for i in lst):

                return '[\n' + ',\n'.join(
                    [
                        pad + '  ' +
                        json.dumps(
                            i,
                            ensure_ascii=False,
                            separators=(',', ': ')
                        )
                        for i in lst
                    ]
                ) + '\n' + pad + ']'


            return json.dumps(
                lst,
                ensure_ascii=False,
                indent=2
            )


        def _encode(obj, indent_level=0):

            pad = '  ' * indent_level


            if isinstance(obj, dict):

                lines = [
                    f'"{k}": {_encode(v, indent_level+1)}'
                    for k,v in obj.items()
                ]

                return (
                    '{\n'
                    + pad + '  '
                    + (',\n'+pad+'  ').join(lines)
                    + '\n'
                    + pad
                    + '}'
                )


            elif isinstance(obj,list):

                return _compact_list(
                    obj,
                    indent_level
                )


            return json.dumps(
                obj,
                ensure_ascii=False
            )


        return iter([_encode(o)])



def save_json(data):

    with open(
        "tvbox_cleaned.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2,
            cls=CompactJSONEncoder
        )


    print("✅ 保存 tvbox_cleaned.json")



if __name__ == "__main__":

    try:

        if len(sys.argv) < 2:

            print(
                "用法: python aowu.py aowu.json"
            )

            sys.exit(1)


        input_file = sys.argv[1]


        print(
            f"📂读取文件: {input_file}"
        )


        raw_text = read_local_json(
            input_file
        )


        # 下载spider
        extract_and_save_spider(
            raw_text
        )


        data = clean_data(
            raw_text
        )


        # 更新spider

        jar_path = "../jar/aowu.jar"


        if os.path.exists(jar_path):

            md5_value = get_md5(
                jar_path
            )


            data["spider"] = (
                f"./jar/aowu.jar;md5;{md5_value}"
            )


            print(
                "🔄 spider更新:",
                data["spider"]
            )


        save_json(data)



    except Exception as e:

        print(
            "❌错误:",
            e
        )
