#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from kirami import KiramiBot

bot = KiramiBot()
app = bot.asgi

if __name__ == "__main__":
    bot.run(app="__mp_main__:app")
