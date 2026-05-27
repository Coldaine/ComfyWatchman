// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.
export const markdownComponents = {
  p: ({ children }) => {
    return <p className="!my-0.5 leading-relaxed text-xs">{children}</p>
  },
  h1: ({ children }) => {
    return <h1 className="text-base font-semibold !my-1">{children}</h1>
  },
  // ... 其他组件配置
};

export const markdownPlugins = {
  rehypePlugins: [
    [rehypeExternalLinks, { target: '_blank' }],
    rehypeKatex
  ],
  remarkPlugins: [remarkGfm, remarkMath]
}; 