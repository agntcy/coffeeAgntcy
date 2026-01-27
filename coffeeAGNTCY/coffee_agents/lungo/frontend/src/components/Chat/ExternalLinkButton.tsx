import React from "react"

interface ExternalLinkButtonProps {
    url: string
    label: string
    iconSrc: string
}

const ExternalLinkButton: React.FC<ExternalLinkButtonProps> = ({ url, label, iconSrc }) => (
    <div className="w-full max-w-[85px] mb-1">
        <button
            className="w-full flex items-center gap-1 border border-gray-300 dark:border-gray-700 rounded px-2 py-1 font-cisco text-xs text-chat-text transition-colors"
            style={{ backgroundColor: "var(--external-link-button-bg)" }}
            onClick={() => window.open(url, "_blank")}
            type="button"
        >
            <img src={iconSrc} alt={label} className="h-4 w-4" />
            {label}
        </button>
    </div>
)


export default ExternalLinkButton


