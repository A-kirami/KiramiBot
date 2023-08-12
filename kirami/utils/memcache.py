"""本模块提供了一个memcache的实例，用于缓存数据"""

from cashews.wrapper import Cache

cache = Cache("kirami")
cache.setup("mem://")
