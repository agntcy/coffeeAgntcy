// ObservabilityDropdown.tsx
import React from "react"

interface ObservabilityDropdownProps {
    grafanaUrl: string
}

const ObservabilityDropdown: React.FC<ObservabilityDropdownProps> = ({ grafanaUrl }) => (
    <div className="w-full max-w-[880px] mb-2">
        <label className="font-semibold text-sm mb-1 block">Observability</label>
        <select
            className="w-full border rounded px-3 py-2"
            onChange={e => {
                if (e.target.value === "grafana") {
                    window.open(grafanaUrl, "_blank")
                }
            }}
            defaultValue=""
        >
            <option value="" disabled>
                Select...
            </option>
            <option value="grafana">Grafana</option>
        </select>
    </div>
)

export default ObservabilityDropdown
