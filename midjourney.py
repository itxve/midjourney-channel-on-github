import requests, re, os


channelUrl = os.getenv("Channel")
authorization = os.getenv("Authorization")
count = os.getenv("Count")

print(
    "count: %s ,channerl %s ,authorization : %s , input_token : %s"
    % (count, channelUrl, authorization, count)
)


if count is not None:
    count = int(count)
    if count > 200:
        count = 200
else:
    count = 20


#
def get_channel(url):
    if re.compile("^[0-9]*$").match(url) is None:
        rec = re.compile(r"https://discord.com/channels/[0-9]*/([0-9]*)")
        if rec.match(url) is None:
            return url
        return rec.match(url).group(1)
    else:
        return url


channel = get_channel(channelUrl)
headers = {"authorization": authorization}


# some functions


def get_data(limit, headers, *, before=None, after=None):
    url = f"https://discord.com/api/v9/channels/{channel}/messages?limit={limit}"
    if before is not None:
        url += f"&before={before}"
    if after is not None:
        url += f"&after={after}"
    print("get url:[  %s ]" % url)
    result = requests.get(url, headers=headers)
    if result.status_code == 200:
        return result.json()
    else:
        print("error %s" % result.json())


# 「有喜欢」组件(说明是单张图)
def has_favorite(components, label="Favorite"):
    for component in components:
        for child in component["components"]:
            if "label" in child and child["label"] == label:
                return True
            else:
                continue
    return False


def data2map_dict(data):
    f_data = {}

    for indx, item in enumerate(data):
        id = item["id"]
        if indx == 0:
            f_data["after"] = id
        elif indx == len(data) - 1:
            f_data["before"] = id

        if has_favorite(item["components"]):
            content = item["content"]
            content = re.compile(r"\*\*(.*)\*\*").match(content).group(1)  # 提示词

            def map2data(attachment):
                proxy_url = attachment["proxy_url"]
                real_url = attachment["url"]
                obj = {"content": content, "proxy_url": proxy_url, "real_url": real_url}
                return obj

            f_data[id] = list(map(map2data, item["attachments"]))
    return f_data


def data2map_list(data):
    f_list = []
    before_id = None

    for indx, item in enumerate(data):
        if indx == len(data) - 1:  # before ID向上查找 (最后一个元素是这批最早的数据)
            before_id = item["id"]

        if has_favorite(item["components"]):
            content = item["content"]
            content = re.compile(r"\*\*(.*)\*\*").match(content).group(1)  # 提示词

            def map_data(attachment):
                proxy_url = attachment["proxy_url"]
                real_url = attachment["url"]
                obj = {"content": content, "proxy_url": proxy_url, "real_url": real_url}
                return obj

            f_list += list(map(map_data, item["attachments"]))

    return before_id, f_list


def write2file(data):
    with open("README.md", "w") as reme:
        text = """<p style="display:flex;flex-direction:column;">"""
        for img_text in data:
            url = img_text["proxy_url"]
            content = img_text["content"]
            content = f"""{content}"""
            text += f"""<img src="{url}" title="{content}" />"""
        text += "</p>"
        reme.write(text)


if __name__ == "__main__":
    limit = 50

    def fetch(ls, before_id=None):
        if len(ls) >= count:
            return
        rt = get_data(limit, headers, before=before_id)
        if rt is not None and len(rt) > 0:
            before_id, f_list = data2map_list(rt)
            if len(f_list) == 0:
                fetch(ls, before_id)
            else:
                ls += f_list
                if len(ls) < count:
                    fetch(ls, before_id)

    arr = []
    fetch(arr)
    # 写入readme
    write2file(arr)
