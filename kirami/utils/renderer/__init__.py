"""本模块提供了一个渲染器，用于将 jinja2 模板和 markdown 渲染为 html"""

from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, Literal

from jinja2 import Environment
from markdown_it import MarkdownIt
from markdown_it.common.utils import escapeHtml, unescapeAll
from markdown_it.renderer import RendererHTML
from markdown_it.token import Token
from markdown_it.utils import EnvType, OptionsDict
from mdit_py_emoji import emoji_plugin
from mdit_py_plugins.dollarmath.index import dollarmath_plugin
from mdit_py_plugins.tasklists import tasklists_plugin
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name


class CustomRendererHTML(RendererHTML):
    def fence(
        self, tokens: Sequence[Token], idx: int, _options: OptionsDict, env: EnvType
    ) -> str:
        token = tokens[idx]
        info = unescapeAll(token.info).strip() if token.info else ""
        langName = info.split(maxsplit=1)[0] if info else ""

        lexer = get_lexer_by_name(langName)
        formatter = HtmlFormatter(style=env.get("theme") or "default")

        return highlight(token.content, lexer, formatter) or escapeHtml(token.content)


class Renderer:
    env: ClassVar[Environment] = Environment(autoescape=True, enable_async=True)
    md: ClassVar[MarkdownIt] = (
        MarkdownIt("gfm-like", renderer_cls=CustomRendererHTML)
        .use(emoji_plugin)
        .use(tasklists_plugin)
        .use(dollarmath_plugin)
    )

    @classmethod
    async def template(
        cls, tpl: str | Path, *, env: Environment | None = None, **kwargs
    ) -> str:
        """将 jinja2 模板渲染为 html。

        ### 参数
            tpl: 模板字符串或文件路径

            env: jinja2 环境，默认为类属性 env

            **kwargs: 传递给渲染后的 html 的参数

        ### 返回
            html 字符串
        """
        if isinstance(tpl, Path):
            tpl = tpl.read_text(encoding="utf-8")
        env = env or cls.env
        template = env.from_string(tpl)
        return await template.render_async(**kwargs)

    @classmethod
    async def markdown(
        cls,
        md: str | Path,
        theme: Literal["light", "dark"] = "light",
        highlight: str | None = "auto",
        extra: str = "",
        only_md: bool = False,
        **kwargs,
    ) -> str:
        """将 markdown 渲染为 html。

        ### 参数
            md: markdown 字符串或文件路径

            theme: 主题，可选值为 "light" 或 "dark"，默认为 "light"

            highlight: 代码高亮主题，可选值为 "auto" 或 pygments 支持的主题，默认为 "auto"

            extra: 额外的 head 标签内容，可以是 meta 标签、link 标签、script 标签、style 标签等

            only_md: 是否只渲染 markdown，不渲染为完整的 html

            **kwargs: 传递给渲染后的 html 的参数

        ### 返回
            html 字符串
        """
        if isinstance(md, Path):
            md = md.read_text(encoding="utf-8")
        env = {}
        if highlight == "auto":
            env["theme"] = "xcode" if theme == "light" else "lightbulb"
        html = cls.md.render(md, env=env)
        if only_md:
            return await cls.template(html, **kwargs)
        base_path = Path(__file__).parent / "template"
        return await cls.template(
            base_path / "markdown.html",
            markdown=html,
            theme=theme,
            extra=extra,
            base_path=base_path,
            **kwargs,
        )
