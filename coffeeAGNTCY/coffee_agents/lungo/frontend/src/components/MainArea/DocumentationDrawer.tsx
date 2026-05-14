/**
 * Copyright AGNTCY Contributors (https://github.com/agntcy)
 * SPDX-License-Identifier: Apache-2.0
 *
 * Floating workflow/pattern documentation panel over the main graph area.
 * Catalog workflow name for GET /agentic-workflows/{name}/documentation/ is
 * resolved via `getCatalogWorkflowNameForPattern` (implemented) or
 * `selectedPlaceholderPatternName` (placeholder).
 **/

import React, {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react"
import Accordion from "@mui/material/Accordion"
import AccordionDetails from "@mui/material/AccordionDetails"
import AccordionSummary from "@mui/material/AccordionSummary"
import Typography from "@mui/material/Typography"
import ExpandMoreIcon from "@mui/icons-material/ExpandMore"
import DescriptionOutlined from "@mui/icons-material/DescriptionOutlined"
import ReactMarkdown from "react-markdown"
import rehypeSanitize from "rehype-sanitize"
import { fetchWorkflowDocumentation } from "@/utils/agenticWorkflowsApi"
import { getCatalogWorkflowNameForPattern } from "@/utils/sidebarHierarchy"
import { PATTERNS, type PatternType } from "@/utils/patternUtils"
import { cn } from "@/utils/cn"

export type DocumentationDrawerMode = "implemented" | "placeholder"

type VisualState = "collapsed" | "expanded" | "full"

const VISUAL_ORDER: VisualState[] = ["collapsed", "expanded", "full"]

/** Left-click: delay before treating as single “forward” (double-click cancels). */
const CLICK_SINGLE_DELAY_MS = 280
/** Right `contextmenu`: max gap (ms) between two events to count as “double” → forward. */
const RIGHT_DOUBLE_WINDOW_MS = 450
/** Panel `transform` / `width` transition duration (ms). */
const PANEL_TRANSITION_MS = 300

export interface DocumentationDrawerProps {
    mode: DocumentationDrawerMode
    selectedPattern: PatternType
    selectedPlaceholderPatternName: string | null
}

const stepForward = (v: VisualState): VisualState =>
    VISUAL_ORDER[(VISUAL_ORDER.indexOf(v) + 1) % VISUAL_ORDER.length]!

const stepBackward = (v: VisualState): VisualState =>
    VISUAL_ORDER[(VISUAL_ORDER.indexOf(v) + 2) % VISUAL_ORDER.length]!

const DocumentationDrawer: React.FC<DocumentationDrawerProps> = ({
    mode,
    selectedPattern,
    selectedPlaceholderPatternName,
}) => {
    const [visual, setVisual] = useState<VisualState>("collapsed")
    const [doc, setDoc] = useState<Awaited<
        ReturnType<typeof fetchWorkflowDocumentation>
    > | null>(null)
    const [loadError, setLoadError] = useState<string | null>(null)
    const [loading, setLoading] = useState(false)

    const leftClickTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
    const lastRightDownRef = useRef<number>(0)

    /** Keeps the panel mounted while sliding out after collapse. */
    const [panelMounted, setPanelMounted] = useState(false)
    /** true = sheet on-screen (`translate-x-0`); false = off to the right. */
    const [panelSlideOpen, setPanelSlideOpen] = useState(false)
    const panelRef = useRef<HTMLDivElement | null>(null)
    const prevWantsPanelRef = useRef(false)

    const workflowName = useMemo(() => {
        if (selectedPattern === PATTERNS.NO_WORKFLOW_IMPLEMENTATION) {
            return selectedPlaceholderPatternName
        }
        return getCatalogWorkflowNameForPattern(selectedPattern)
    }, [selectedPattern, selectedPlaceholderPatternName])

    const effectiveVisual: VisualState =
        mode === "placeholder" ? "full" : visual

    const wantsPanel = effectiveVisual !== "collapsed"

    useEffect(() => {
        if (mode === "implemented") {
            setVisual("collapsed")
        }
    }, [mode])

    useEffect(() => {
        if (!workflowName) {
            setDoc(null)
            setLoadError(null)
            setLoading(false)
            return
        }

        const ac = new AbortController()
        setLoading(true)
        setLoadError(null)

        fetchWorkflowDocumentation(workflowName, ac.signal)
            .then((res) => {
                setDoc(res)
                setLoading(false)
            })
            .catch((err: unknown) => {
                if (ac.signal.aborted) return
                setDoc(null)
                setLoading(false)
                setLoadError(
                    err instanceof Error ? err.message : "Failed to load documentation",
                )
            })

        return () => ac.abort()
    }, [workflowName])

    const applyGestureForward = useCallback(() => {
        if (mode === "placeholder") return
        setVisual((v) => stepForward(v))
    }, [mode])

    const applyGestureBackward = useCallback(() => {
        if (mode === "placeholder") return
        setVisual((v) => stepBackward(v))
    }, [mode])

    const clearLeftTimer = () => {
        if (leftClickTimerRef.current) {
            clearTimeout(leftClickTimerRef.current)
            leftClickTimerRef.current = null
        }
    }

    const onDocIconClick = (e: React.MouseEvent) => {
        if (mode === "placeholder") return
        if (e.button !== 0) return

        if (e.detail === 2) {
            clearLeftTimer()
            applyGestureBackward()
            return
        }

        if (e.detail === 1) {
            clearLeftTimer()
            leftClickTimerRef.current = setTimeout(() => {
                leftClickTimerRef.current = null
                applyGestureForward()
            }, CLICK_SINGLE_DELAY_MS)
        }
    }

    const onDocIconContextMenu = (e: React.MouseEvent) => {
        e.preventDefault()
        if (mode === "placeholder") return

        const now = Date.now()
        if (now - lastRightDownRef.current < RIGHT_DOUBLE_WINDOW_MS) {
            lastRightDownRef.current = 0
            applyGestureForward()
        } else {
            lastRightDownRef.current = now
            applyGestureBackward()
        }
    }

    useEffect(() => {
        if (!wantsPanel) {
            if (panelMounted) {
                setPanelSlideOpen(false)
            }
            prevWantsPanelRef.current = false
            return
        }

        const entering = !prevWantsPanelRef.current
        prevWantsPanelRef.current = true
        setPanelMounted(true)

        if (mode === "placeholder") {
            setPanelSlideOpen(true)
            return
        }

        if (entering) {
            setPanelSlideOpen(false)
            const id = requestAnimationFrame(() => {
                requestAnimationFrame(() => setPanelSlideOpen(true))
            })
            return () => cancelAnimationFrame(id)
        }

        setPanelSlideOpen(true)
    }, [wantsPanel, effectiveVisual, mode, panelMounted])

    const onPanelTransitionEnd = (e: React.TransitionEvent<HTMLDivElement>) => {
        if (e.target !== panelRef.current) return
        if (e.propertyName !== "transform" && e.propertyName !== "width") return
        if (!wantsPanel && !panelSlideOpen) {
            setPanelMounted(false)
        }
    }

    const panelWidthClass =
        effectiveVisual === "expanded"
            ? "w-[30%] min-w-[260px] max-w-xl"
            : effectiveVisual === "full"
                ? "w-full"
                : "w-[30%] min-w-[260px] max-w-xl"

    const preamble = doc?.sections.find((s) => s.heading === "preamble")
    const accordionSections =
        doc?.sections.filter((s) => s.heading !== "preamble") ?? []

    const transitionMs = `${PANEL_TRANSITION_MS}ms`

    const showFab =
        mode === "implemented" &&
        effectiveVisual === "collapsed" &&
        !panelMounted

    return (
        <div
            className="pointer-events-none absolute inset-0 z-[50] flex justify-end"
            aria-hidden={false}
        >
            {showFab && (
                <div className="pointer-events-auto absolute right-3 top-3">
                    <button
                        type="button"
                        className={cn(
                            "flex h-10 w-10 items-center justify-center rounded-lg border border-action-background bg-app-background text-sidebar-text shadow-md hover:bg-sidebar-item-selected",
                        )}
                        aria-label="Documentation"
                        onClick={onDocIconClick}
                        onContextMenu={onDocIconContextMenu}
                    >
                        <DescriptionOutlined fontSize="small" />
                    </button>
                </div>
            )}

            {panelMounted && (
                <div
                    ref={panelRef}
                    onTransitionEnd={onPanelTransitionEnd}
                    className={cn(
                        "pointer-events-auto absolute right-0 top-0 z-[51] flex h-full flex-col border-l border-action-background bg-app-background shadow-xl",
                        "ease-out motion-reduce:transition-none",
                        panelWidthClass,
                        panelSlideOpen
                            ? "translate-x-0 opacity-100"
                            : "translate-x-full opacity-100",
                        wantsPanel ? "pointer-events-auto" : "pointer-events-none",
                    )}
                    style={{
                        transitionProperty: "transform, width",
                        transitionDuration: transitionMs,
                    }}
                >
                    <div className="flex flex-none items-center gap-2 border-b border-action-background px-3 py-2">
                        <button
                            type="button"
                            className="flex h-9 w-9 flex-none items-center justify-center rounded-md hover:bg-sidebar-item-selected"
                            aria-label="Documentation"
                            onClick={onDocIconClick}
                            onContextMenu={onDocIconContextMenu}
                        >
                            <DescriptionOutlined fontSize="small" />
                        </button>
                        <Typography className="flex-1 truncate" variant="subtitle1">
                            {doc?.title ?? workflowName ?? "Documentation"}
                        </Typography>
                    </div>

                    <div className="min-h-0 flex-1 overflow-y-auto px-3 py-3">
                        {loading && (
                            <Typography variant="body2" color="text.secondary">
                                Loading…
                            </Typography>
                        )}
                        {loadError && !loading && (
                            <Typography variant="body2" color="error">
                                {loadError}
                            </Typography>
                        )}
                        {!loading && !loadError && doc && (
                            <>
                                {preamble && (
                                    <div className="documentation-markdown mb-4 max-w-none text-sm">
                                        <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
                                            {preamble.body_markdown}
                                        </ReactMarkdown>
                                    </div>
                                )}
                                {accordionSections.map((section) => (
                                    <Accordion
                                        key={section.anchor}
                                        defaultExpanded
                                        disableGutters
                                        className="mb-1 border border-action-background shadow-none before:hidden"
                                    >
                                        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                            <Typography variant="subtitle2">
                                                {section.heading}
                                            </Typography>
                                        </AccordionSummary>
                                        <AccordionDetails>
                                            <div className="documentation-markdown max-w-none text-sm">
                                                <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
                                                    {section.body_markdown}
                                                </ReactMarkdown>
                                            </div>
                                        </AccordionDetails>
                                    </Accordion>
                                ))}
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}

export default DocumentationDrawer