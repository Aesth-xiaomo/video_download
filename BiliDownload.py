import os
import sys
import requests
import re
import json
import random
import subprocess
import time
import hashlib


class BiliDownload():
    def __init__(self, target):
        self.target = target
        self.user_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20130406 Firefox/23.0',
                            'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:18.0) Gecko/20100101 Firefox/18.0',
                            'IBM WebExplorer /v0.94', 'Galaxy/1.0 [en] (Mac OS X 10.5.6; U; en)',
                            'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
                            'Opera/9.80 (Windows NT 6.0) Presto/2.12.388 Version/12.14',
                            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; TheWorld)',
                            'Opera/9.52 (Windows NT 5.0; U; en)',
                            'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.2pre) Gecko/2008071405 GranParadiso/3.0.2pre',
                            'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.458.0 Safari/534.3',
                            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/4.0.211.4 Safari/532.0',
                            'Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.7.39 Version/11.00',
                            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36']
        if not os.path.exists("data/new_video"):
            os.makedirs("data/new_video")

    @staticmethod
    def create_md5():
        m = hashlib.md5()
        m.update(bytes(str(time.time()), encoding='utf-8'))
        return m.hexdigest()

    def get_detail(self):
        detail = requests.get(self.target, headers={"User-Agent": random.choice(self.user_agents)}, timeout=None).text
        origin_txt = re.findall(r'<script>window.__playinfo__=(\{.*?\})</script>', detail, re.S)[0]
        origin_json = json.loads(origin_txt, encoding='utf-8')
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Origin': 'https://www.bilibili.com',
            'Referer': self.target,
        }
        if 'durl' in origin_json['data']:
            self.durl_download(origin_json['data'], headers)
        if 'dash' in origin_json['data']:
            self.dash_download(origin_json['data'], headers)

    def durl_download(self, video_json, headers):
        if not os.path.exists("data/durl_video"):
            os.makedirs("data/durl_video")
        urls = video_json['durl']
        print("该视频一共有%s段" % len(urls))
        for i, data in enumerate(urls):
            url = data['url']
            video_path = 'data/durl_video/%s.mp4' % i
            # 制作视频拼接顺序文档
            with open('data/durl_video/temp.txt', 'a', encoding="utf-8") as temp_f:
                temp_f.write("file '%s.mp4'" % str(i) + "\n")
            print("正在下载第%s段" % (i+1))
            self.download_bin(url, video_path, headers)
        # 合并分段视频
        try:
            ffmpeg_command = ["ffmpeg", "-f", "concat", "-i", "data/durl_video/temp.txt", "-c", "copy", "data/new_video/%s.mp4" % self.create_md5()]
            subprocess.run(ffmpeg_command)
            print("视频拼接完成！")
        except Exception as e:
            print(e)

    @staticmethod
    def download_bin(url, tpath, headers):
        chunk = 1024
        try:
            # 根据解析出的视频url获取到视频二进制格式
            response = requests.get(url, headers=headers, verify=False, stream=True)
            # 分段写入视频二进制
            with open(tpath, 'wb') as file:
                for item in response.iter_content(chunk):
                    file.write(item)  # 写入视频
                    file.flush()  # 清空缓存
        except Exception as e:
            print(e)

    def dash_download(self, video_json, headers):
        if not os.path.exists("data/dash_video"):
            os.makedirs("data/dash_video")
        v_url = video_json['dash']['video'][0]['baseUrl']
        a_url = video_json['dash']['audio'][0]['baseUrl']
        video_path = 'data/dash_video/temp.mp4'
        audio_path = 'data/dash_video/temp.mp3'

        print("正在下载视频——————")
        self.download_bin(v_url, video_path, headers)
        print("正在下载音频——————")
        self.download_bin(a_url, audio_path, headers)

        # 合并音视频
        try:
            ffmpeg_command = ["ffmpeg", "-i", 'data/dash_video/temp.mp3', "-i", 'data/dash_video/temp.mp4', "data/new_video/final.mp4"]
            subprocess.run(ffmpeg_command)
            print("视频拼接完成！")
        except Exception as e:
            print(e)

    def run(self):
        self.get_detail()


if __name__ == '__main__':
    target_url = sys.argv[1]
    spider = BiliDownload(target_url)
    spider.run()
