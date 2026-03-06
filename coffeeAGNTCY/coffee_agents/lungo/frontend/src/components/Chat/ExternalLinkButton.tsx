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

const ExternalLinkButton: React.FC<ExternalLinkButtonProps> = ({
  url,
  label,
  iconSrc,
  className,
}) => (
  <a
    href={url}
    target="_blank"
    rel="noopener noreferrer"
    type="button"
    className={`aaa hover:bg-accent-primary/10 absolute inline-flex max-h-[20px] max-w-[90px] items-center gap-1 rounded-full border border-gray-300 bg-[var(--external-link-button-bg)] px-2 py-1 font-cisco text-xs text-chat-text shadow transition-colors dark:border-gray-700 ${className ?? ""}`}
    style={{ marginLeft: 12 }}
  >
    <img src={iconSrc} alt={label} className="h-4 w-4" />
    {label}
  </a>
)

export default ExternalLinkButton
