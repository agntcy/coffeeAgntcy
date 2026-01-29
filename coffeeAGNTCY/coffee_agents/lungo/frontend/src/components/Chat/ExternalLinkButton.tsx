/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 **/

interface ExternalLinkButtonProps {
    url: string
    label: string
    iconSrc: string
    className?: string
}

const ExternalLinkButton: React.FC<ExternalLinkButtonProps> = ({ url, label, iconSrc, className }) => (
    <button
        className={`absolute inline-flex items-center gap-1 border border-gray-300 dark:border-gray-700 rounded-full px-2 py-1 font-cisco text-xs text-chat-text transition-colors shadow bg-[var(--external-link-button-bg)] hover:bg-accent-primary/10 max-w-[90px] max-h-[20px] ${className ?? ""}`}
        onClick={() => window.open(url, "_blank")}
        type="button"
        style={{ marginLeft: 12 }}
    >
        <img src={iconSrc} alt={label} className="h-4 w-4" />
        {label}
    </button>
)

export default ExternalLinkButton
