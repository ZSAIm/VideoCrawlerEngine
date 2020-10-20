"""
==================================
Name:       fake script
Author:     ZSAIM
Created:    2020-10-18
Recently Update:
Version:    0.1
License:    Apache-2.0
==================================
"""
from script import ScriptBaseClass, dbg


class FakeScript(ScriptBaseClass):
    name = 'fake'
    version = 0.0
    author = 'ZSAIM'
    created_date = '2020/10/18'

    supported_domains = ['fake.script']
    quality_ranking = [0, 1, 2, 3, 4, 5]

    def run(self):
        target = self.options.get('test_target')
        dbg.upload(items=target)
        return target


if __name__ == '__main__':
    # 重载基类
    from script.base import ScriptBaseClass

    # bilibili = Bilibili.test('https://www.bilibili.com/video/av91721893', 100)
    # bilibili = Bilibili.test('https://www.bilibili.com/video/BV167411E7Tn', 100)
    # bilibili = Bilibili.test('https://www.bilibili.com/video/BV1sK411p7vg', 100)
    bilibili = FakeScript.test('https://www.bilibili.com/video/BV14p4y1D7r7', 100)
    print(bilibili)

    # live = BilibiliLive.test('https://live.bilibili.com/910819', 100)
    # print(live)