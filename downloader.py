import enum
from abc import ABC
from typing import Union
import requests
from instagrapi import Client
from pytube import YouTube
from yt_dlp import YoutubeDL
from dataclasses import dataclass
import vk_api
api_key = 'vk1.a.ZdVIZ1GqKtHWBZZ9Pz8Da4PTRLZnBysAgEgF3faaLkZ7XbywX8MsYVgRmc-QXpAn20O4sfKN0Y--vMAucArHM6M25W9PKmB7RSBVdZiaWyhR5jn7szJ0_cN4tLQm0oF5PepVQKSUsTYAwgHD2fZZQfkxlMVi6XIyquKVXyBjP1ivMzCM_udor8MzMQgo_ggy6uB_skXWM2INNOitJdv0vA'
vk_session = vk_api.VkApi(token=api_key)
vk = vk_session.get_api()


class TypeAttachment(enum.Enum):
    VIDEO = 0
    PHOTO = 1


@dataclass
class Attachment:
    type_attachment: TypeAttachment
    file_name: str


@dataclass
class PostInfo:
    attachments: list[Attachment]
    description: Union[str, None]


class Downloader(ABC):
    @staticmethod
    def download(link) -> str:
        pass


# class InstDownloader(Downloader):
#     inst = Client()
#     inst.login('doruqyhipiros8793', 'Gtdv3fghu76')
#
#     @staticmethod
#     def download(link) -> tuple:
#         inst = InstDownloader.inst
#         pk = inst.media_pk_from_url(link)
#         d = inst.media_info(pk).dict()
#         desc = d['caption_text']
#         print(desc)
#         if d['media_type'] == 8:
#             return inst.album_download(int(pk)), desc
#         if d['media_type'] == 1:
#             return [inst.photo_download(int(pk))], desc
#         if d['media_type'] == 2 and d['product_type'] in ('feed', 'clips'):
#             return [inst.video_download(int(pk))], desc


class VkDownloader(Downloader):
    @staticmethod
    def download(link: str) -> PostInfo:
        photos, desc = VkDownloader.get_attachments(link)
        attachments = VkDownloader.download_attachments(photos)
        return PostInfo(attachments, desc)

    @staticmethod
    def get_attachments(link: str) -> tuple[list[dict], str]:
        kwargs = VkDownloader.get_kwargs_from_link(link)
        post = kwargs['w'].replace('wall', '')
        res = vk.wall.getById(posts=[post])
        return res[0]['attachments'], res[0]['text']

    @staticmethod
    def download_attachments(photos: list[dict]) -> list[Attachment]:
        ph = []
        for attachment in photos:
            if attachment['type'] == 'photo':
                max_photo = VkDownloader.get_max_size(attachment['photo'])
                url = max_photo['url']
                r = requests.get(url)
                name = f'{attachment["photo"]["id"]}_{attachment["photo"]["owner_id"]}'
                f = open(name, 'wb')
                f.write(r.content)
                f.close()
                ph.append(Attachment(TypeAttachment.PHOTO, name))
            if attachment['type'] == 'video':
                yt = YoutubeDL()
                link = f'https://vk.com/video?z=video{attachment["video"]["owner_id"]}_{attachment["video"]["id"]}'
                info = yt.extract_info(link, download=False)
                file_path = yt.prepare_filename(info)
                if not file_path.endswith('.NA'):
                    yt.download([link])
                    ph.append(Attachment(TypeAttachment.VIDEO, file_path))

        return ph

    @staticmethod
    def get_max_size(photo: dict):
        max_photo = None
        max_size = 0
        for size in photo['sizes']:
            if max_size < size['height'] * size['width']:
                max_photo = size
                max_size = size['height'] * size['width']
        return max_photo

    @staticmethod
    def get_kwargs_from_link(link: str):
        try:
            args = link.split('?')[1]
            d = {}
            for i in args.split('&'):
                key, item = i.split('=')
                d[key] = item
            return d
        except IndexError:
            return {'w': link.split('wall')[1]}


def resolution_youtube_converter(resolution):
    if resolution is None:
        return 0
    if resolution:
        return int(resolution[:-1])


class YouTubeDownloader(Downloader):
    @staticmethod
    def download(link) -> PostInfo:
        yt = YouTube(link)
        streams = yt.streams.filter(file_extension='mp4')
        stream = YouTubeDownloader.find_highest_resolution(streams)
        file_name = stream.download()
        return PostInfo([file_name], None)

    @staticmethod
    def find_highest_resolution(streams: YouTube.streams):
        highest = streams[0]
        for stream in streams:
            highest_res = resolution_youtube_converter(highest.resolution)
            stream_res = resolution_youtube_converter(stream.resolution)
            if stream_res > highest_res and stream.audio_codec:
                highest = stream
        return highest


# YouTubeDownloader.download('https://www.youtube.com/shorts/YuefdpXIstc')
# VkDownloader.download('https://vk.com/tnull?z=video-72495085_456242138%2Fvideos-72495085%2Fpl_-72495085_-2')
# VkDownloader.download('https://vk.com/feed?w=wall-12353330_13715718')
# VkDownloader.download('https://www.instagram.com/reel/Cqa66C8IBD8/?utm_source=ig_web_copy_link')
# InstDownloader.download('https://www.instagram.com/p/CqpwOJAIpGV/')
