/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Rich `react-markdown` element mapping for the documentation drawer (no
 * extra markdown plugins).
 **/

import type { Components } from "react-markdown"

export const DOCUMENTATION_MARKDOWN_COMPONENTS: Components = {
    h1: ({ children, ...props }) => (
        <h1
            className="mb-3 mt-8 border-b border-sidebar-border pb-2 text-2xl font-bold tracking-tight text-sidebar-text first:mt-0"
            {...props}
        >
            {children}
        </h1>
    ),
    h2: ({ children, ...props }) => (
        <h2
            className="mb-2 mt-6 text-xl font-semibold tracking-tight text-sidebar-text first:mt-0"
            {...props}
        >
            {children}
        </h2>
    ),
    h3: ({ children, ...props }) => (
        <h3
            className="mb-2 mt-5 text-lg font-semibold text-sidebar-text first:mt-0"
            {...props}
        >
            {children}
        </h3>
    ),
    h4: ({ children, ...props }) => (
        <h4
            className="mb-2 mt-4 text-base font-semibold text-sidebar-text first:mt-0"
            {...props}
        >
            {children}
        </h4>
    ),
    h5: ({ children, ...props }) => (
        <h5
            className="mb-1.5 mt-3 text-sm font-semibold uppercase tracking-wide text-sidebar-text first:mt-0"
            {...props}
        >
            {children}
        </h5>
    ),
    h6: ({ children, ...props }) => (
        <h6
            className="mb-1.5 mt-3 text-sm font-semibold text-sidebar-text/95 first:mt-0"
            {...props}
        >
            {children}
        </h6>
    ),
    p: ({ children, ...props }) => (
        <p
            className="mb-3 text-[15px] leading-relaxed text-sidebar-text/95 last:mb-0"
            {...props}
        >
            {children}
        </p>
    ),
    ul: ({ children, ...props }) => (
        <ul
            className="mb-3 list-disc space-y-1.5 pl-5 text-[15px] leading-relaxed text-sidebar-text/95 marker:text-accent-primary"
            {...props}
        >
            {children}
        </ul>
    ),
    ol: ({ children, ...props }) => (
        <ol
            className="mb-3 list-decimal space-y-1.5 pl-5 text-[15px] leading-relaxed text-sidebar-text/95 marker:font-medium marker:text-accent-primary"
            {...props}
        >
            {children}
        </ol>
    ),
    li: ({ children, ...props }) => (
        <li className="pl-0.5 [&>p]:mb-2 [&>p:last-child]:mb-0" {...props}>
            {children}
        </li>
    ),
    strong: ({ children, ...props }) => (
        <strong className="font-semibold text-sidebar-text" {...props}>
            {children}
        </strong>
    ),
    em: ({ children, ...props }) => (
        <em className="italic text-sidebar-text/95" {...props}>
            {children}
        </em>
    ),
    a: ({ children, ...props }) => (
        <a
            className="font-medium text-accent-primary underline underline-offset-2 hover:opacity-90"
            target="_blank"
            rel="noopener noreferrer"
            {...props}
        >
            {children}
        </a>
    ),
    code: ({ className, children, ...props }) => {
        return (
            <code className={className} {...props}>
                {children}
            </code>
        )
    },
    pre: ({ children, ...props }) => (
        <pre
            className="mb-3 overflow-x-auto rounded-md border border-sidebar-border bg-node-background p-3 font-mono text-sm leading-relaxed text-node-text-primary"
            {...props}
        >
            {children}
        </pre>
    ),
    blockquote: ({ children, ...props }) => (
        <blockquote
            className="mb-3 border-l-4 border-accent-primary py-0.5 pl-3 text-[15px] italic text-sidebar-text/90"
            {...props}
        >
            {children}
        </blockquote>
    ),
    hr: (props) => (
        <hr
            className="my-6 border-0 border-t border-sidebar-border opacity-90"
            {...props}
        />
    ),
    table: ({ children, ...props }) => (
        <div className="mb-3 w-full overflow-x-auto">
            <table
                className="w-full min-w-[16rem] border-collapse text-left text-[14px] text-sidebar-text/95"
                {...props}
            >
                {children}
            </table>
        </div>
    ),
    thead: ({ children, ...props }) => (
        <thead className="border-b border-sidebar-border bg-node-background/80" {...props}>
            {children}
        </thead>
    ),
    th: ({ children, ...props }) => (
        <th className="border border-sidebar-border px-2 py-1.5 font-semibold" {...props}>
            {children}
        </th>
    ),
    td: ({ children, ...props }) => (
        <td className="border border-sidebar-border px-2 py-1.5 align-top" {...props}>
            {children}
        </td>
    ),
}