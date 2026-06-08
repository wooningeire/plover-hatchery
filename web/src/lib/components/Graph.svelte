<script lang="ts">
    import { onMount, untrack } from "svelte";
    import * as d3 from "d3";
    import FlagControls, { type FlagSettings } from "$lib/components/FlagControls.svelte";
    import { linkPathSegment, linkPathYMax } from "./graph";

    type NodeData = {
        id: number,
        x: number,
        y: number,
        color: string,
    };

    type LinkData = {
        source: number,
        target: number,
        keys: string[],
        id: string,
        opacity: number,
        strokeWidth: number,
        dashArray: string | null,
    };

    type GraphData = {
        nodes: number[],
        translation_nodes?: number[],
        transitions: {
            src_node_id: number,
            dst_node_id: number,
            keys_costs: {
                key: string,
                cost: number,
                flags?: string[],
            }[],
        }[],
    };

    type BreakdownPathStep = {
        sophs: string[],
        chord: string,
        nodes: number[],
    };

    type BreakdownPath = {
        path: BreakdownPathStep[],
    };

    let {
        data,
        highlightData = null,
    }: {
        data: GraphData,
        highlightData?: BreakdownPath[] | null,
    } = $props();

    const NODE_RADIUS = 25;
    const NODE_SPACING = 200;
    const VIEWBOX_HEIGHT = 600;
    const VIEWBOX_PADDING_X = 50;
    const VIEWBOX_PADDING_Y = VIEWBOX_HEIGHT / 2;
    const UNFLAGGED_KEY = "(unflagged)";
    const LOCAL_STORAGE_KEY = "flagControlsSettings";
    const DEFAULT_FLAG_SETTINGS: FlagSettings = {
        opacity: 1,
        strokeWidth: 4,
        dashed: false,
        dashLength: 5,
    };

    let svg = $state<SVGSVGElement | undefined>(undefined);
    let mainGroup = $state<d3.Selection<SVGGElement, unknown, null, undefined> | null>(null);
    let flagSettings = $state<Record<string, FlagSettings>>(loadFlagSettings());
    let uniqueFlags = $state<string[]>([]);

    const translationNodesSet = $derived(new Set(data.translation_nodes ?? []));
    const viewBoxWidth = $derived(
        Math.max(
            800,
            Math.max(1, data.nodes.length - 1) * NODE_SPACING + VIEWBOX_PADDING_X * 2,
        ),
    );
    const viewBox = $derived(`0 0 ${viewBoxWidth} ${VIEWBOX_HEIGHT}`);
    const colorScale = d3.scaleOrdinal(d3.schemeTableau10);

    onMount(() => {
        if (svg === undefined) {
            return;
        }

        const svgElement = d3.select(svg);
        const group = svgElement.append("g");
        mainGroup = group;

        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 4])
            .on("zoom", (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
                group.attr("transform", event.transform.toString());
            });

        svgElement.call(zoom);
    });

    $effect(() => {
        const settingsSnapshot = JSON.stringify(flagSettings);
        try {
            localStorage.setItem(LOCAL_STORAGE_KEY, settingsSnapshot);
        } catch (error) {
            console.warn("Failed to save flag settings to localStorage:", error);
        }
    });

    $effect(() => {
        if (!data?.transitions) {
            return;
        }

        const flags = new Set<string>();
        data.transitions.forEach((transition) => {
            transition.keys_costs.forEach((keyCost) => {
                keyCost.flags?.forEach((flag) => flags.add(flag));
            });
        });

        const newFlags = Array.from(flags).sort();

        untrack(() => {
            newFlags.forEach((flag) => {
                if (flagSettings[flag] === undefined) {
                    flagSettings[flag] = { ...DEFAULT_FLAG_SETTINGS };
                }
            });
        });

        uniqueFlags = [UNFLAGGED_KEY, ...newFlags];
    });

    $effect(() => {
        if (!data?.nodes || !data.transitions || mainGroup === null) {
            return;
        }

        mainGroup.selectAll("*").remove();

        const nodes: NodeData[] = data.nodes.map((id, index) => ({
            id,
            x: VIEWBOX_PADDING_X + index * NODE_SPACING,
            y: VIEWBOX_PADDING_Y,
            color: colorScale(id.toString()),
        }));
        const nodeMap = new Map(nodes.map((node) => [node.id, node]));
        const links = buildLinks(data, flagSettings);
        const group = mainGroup;
        const defsInGroup = group.append("defs");

        links.forEach((link) => {
            const source = nodeMap.get(link.source);
            const target = nodeMap.get(link.target);
            if (source === undefined || target === undefined) {
                return;
            }

            const gradient = defsInGroup.append("linearGradient")
                .attr("id", link.id)
                .attr("gradientUnits", "userSpaceOnUse")
                .attr("x1", source.x)
                .attr("y1", source.y)
                .attr("x2", target.x)
                .attr("y2", target.y);

            gradient.append("stop")
                .attr("offset", "0%")
                .attr("stop-color", source.color);

            gradient.append("stop")
                .attr("offset", "100%")
                .attr("stop-color", target.color);
        });

        group.append("g")
            .selectAll("path")
            .data(links)
            .join("path")
            .attr("fill", "none")
            .attr("stroke", (link) => `url(#${link.id})`)
            .attr("stroke-opacity", (link) => link.opacity * 0.6)
            .attr("stroke-width", (link) => link.strokeWidth)
            .attr("stroke-dasharray", (link) => link.dashArray)
            .attr("d", (link) => {
                const source = nodeMap.get(link.source);
                const target = nodeMap.get(link.target);

                return source !== undefined && target !== undefined
                    ? linkPathSegment(source.x, source.y, target.x, target.y)
                    : "";
            });

        const highlights = buildHighlights(highlightData, nodeMap);
        const highlightGroup = group.append("g").attr("class", "highlights");

        highlightGroup.selectAll("path")
            .data(highlights.links)
            .join("path")
            .attr("fill", "none")
            .attr("stroke", "red")
            .attr("stroke-width", 6)
            .attr("stroke-opacity", 0.8)
            .attr("d", (link) => {
                const source = nodeMap.get(link.source);
                const target = nodeMap.get(link.target);

                return source !== undefined && target !== undefined
                    ? linkPathSegment(source.x, source.y, target.x, target.y)
                    : "";
            });

        highlightGroup.selectAll("text")
            .data(highlights.links)
            .join("text")
            .attr("font-family", "Atkinson Hyperlegible Next")
            .attr("fill", "red")
            .attr("font-weight", "bold")
            .attr("text-anchor", "middle")
            .attr("x", (link) => {
                const source = nodeMap.get(link.source);
                const target = nodeMap.get(link.target);

                return source !== undefined && target !== undefined
                    ? (source.x + target.x) / 2
                    : 0;
            })
            .attr("y", (link) => {
                const source = nodeMap.get(link.source);
                const target = nodeMap.get(link.target);

                return source !== undefined && target !== undefined
                    ? linkPathYMax(source.x, source.y, target.x, target.y) - 15
                    : 0;
            })
            .style("font-size", "2rem")
            .style("text-shadow", "0 0 4px white")
            .text((link) => link.chord);

        group.append("g")
            .selectAll("text")
            .data(links)
            .join("text")
            .attr("font-family", "Atkinson Hyperlegible Next")
            .attr("font-size", 16)
            .attr("fill", "#333")
            .attr("font-weight", "normal")
            .attr("text-anchor", "middle")
            .attr("x", (link) => {
                const source = nodeMap.get(link.source);
                const target = nodeMap.get(link.target);

                return source !== undefined && target !== undefined
                    ? (source.x + target.x) / 2
                    : 0;
            })
            .attr("y", (link) => {
                const source = nodeMap.get(link.source);
                const target = nodeMap.get(link.target);

                return source !== undefined && target !== undefined
                    ? linkPathYMax(source.x, source.y, target.x, target.y) + 5
                    : 0;
            })
            .style("opacity", (link) => link.opacity)
            .text((link) => link.keys.join(", "));

        const nodeGroups = group.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("transform", (node) => `translate(${node.x},${node.y})`);

        nodeGroups.append("circle")
            .attr("r", NODE_RADIUS)
            .attr("fill", (node) => node.color)
            .attr("stroke", (node) => node.color)
            .attr("stroke-opacity", 0.5)
            .attr("stroke-width", (node) => translationNodesSet.has(node.id) ? 36 : 0);

        nodeGroups.append("circle")
            .filter((node) => highlights.nodes.has(node.id))
            .attr("r", NODE_RADIUS)
            .attr("fill", "none")
            .attr("stroke", "#f00")
            .attr("stroke-opacity", 0.8)
            .attr("stroke-width", 6);

        nodeGroups.append("text")
            .attr("dy", 5)
            .attr("text-anchor", "middle")
            .attr("fill", "white")
            .attr("font-family", "sans-serif")
            .attr("font-weight", "bold")
            .text((node) => node.id);
    });

    function loadFlagSettings(): Record<string, FlagSettings> {
        if (typeof localStorage === "undefined") {
            return { [UNFLAGGED_KEY]: { ...DEFAULT_FLAG_SETTINGS } };
        }

        try {
            const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
            if (stored !== null) {
                const parsed = JSON.parse(stored);
                if (parsed[UNFLAGGED_KEY] === undefined) {
                    parsed[UNFLAGGED_KEY] = { ...DEFAULT_FLAG_SETTINGS };
                }

                return parsed;
            }
        } catch (error) {
            console.warn("Failed to load flag settings from localStorage:", error);
        }

        return { [UNFLAGGED_KEY]: { ...DEFAULT_FLAG_SETTINGS } };
    }

    function buildLinks(
        graphData: GraphData,
        settings: Record<string, FlagSettings>,
    ) {
        return graphData.transitions.map((transition, index) => {
            const visibleKeyData = transition.keys_costs.map((keyCost) => {
                const associatedFlags = keyCost.flags ?? [];
                const flagDrivenSettings = associatedFlags.length > 0
                    ? associatedFlags.map((flag) => settings[flag] ?? DEFAULT_FLAG_SETTINGS)
                    : [settings[UNFLAGGED_KEY] ?? DEFAULT_FLAG_SETTINGS];
                const isDashed = flagDrivenSettings.some((setting) => setting.dashed);
                const dashLength = isDashed
                    ? Math.max(
                        ...flagDrivenSettings
                            .filter((setting) => setting.dashed)
                            .map((setting) => setting.dashLength),
                    )
                    : 0;

                return {
                    key: keyCost.key,
                    cost: keyCost.cost,
                    opacity: Math.min(...flagDrivenSettings.map((setting) => setting.opacity)),
                    strokeWidth: Math.max(...flagDrivenSettings.map((setting) => setting.strokeWidth)),
                    dashed: isDashed,
                    dashLength,
                };
            }).filter((keyData) => keyData.opacity > 0);

            if (visibleKeyData.length === 0) {
                return null;
            }

            const isDashed = visibleKeyData.some((keyData) => keyData.dashed);
            const dashLength = isDashed
                ? Math.max(...visibleKeyData.filter((keyData) => keyData.dashed).map((keyData) => keyData.dashLength))
                : 0;

            return {
                source: transition.src_node_id,
                target: transition.dst_node_id,
                keys: visibleKeyData.map((keyData) => `${keyData.key} (${keyData.cost})`),
                id: `link-${index}`,
                opacity: Math.max(...visibleKeyData.map((keyData) => keyData.opacity)),
                strokeWidth: Math.max(...visibleKeyData.map((keyData) => keyData.strokeWidth)),
                dashArray: isDashed ? `${dashLength},${dashLength * 0.5}` : null,
            };
        }).filter((link): link is LinkData => link !== null);
    }

    function buildHighlights(
        paths: BreakdownPath[] | null,
        nodeMap: Map<number, NodeData>,
    ) {
        const nodes = new Set<number>();
        const links: { source: number, target: number, chord: string }[] = [];
        const linkKeys = new Set<string>();

        if (paths === null) {
            return { nodes, links };
        }

        pathLoop:
        for (const pathData of paths) {
            const pathLinks: { source: number, target: number, chord: string }[] = [];
            const pathNodes = new Set<number>();

            for (const step of pathData.path) {
                for (let index = 0; index < step.nodes.length - 1; index += 1) {
                    const source = step.nodes[index];
                    const target = step.nodes[index + 1];

                    if (!nodeMap.has(source) || !nodeMap.has(target)) {
                        continue pathLoop;
                    }

                    pathLinks.push({
                        source,
                        target,
                        chord: index === 0 ? step.chord : "...",
                    });
                    pathNodes.add(source);
                    pathNodes.add(target);
                }
            }

            pathLinks.forEach((link) => {
                const key = `${link.source}-${link.target}`;
                if (!linkKeys.has(key)) {
                    linkKeys.add(key);
                    links.push(link);
                }
            });
            pathNodes.forEach((node) => nodes.add(node));
        }

        return { nodes, links };
    }
</script>

<div class="graph">
    <FlagControls flags={uniqueFlags} bind:settings={flagSettings} />

    <div class="graph-container">
        <svg
            bind:this={svg}
            {viewBox}
            preserveAspectRatio="xMidYMid meet"
        ></svg>
    </div>
</div>

<style lang="scss">
    .graph {
        display: grid;
        grid-template-rows: auto minmax(0, 1fr);

        width: 100%;
        height: 100%;
        min-width: 0;
        min-height: 0;
    }

    .graph-container {
        min-width: 0;
        min-height: 0;
        overflow: hidden;

        border-radius: 0.25rem;
        background-color: oklch(0.98 0.003 150);
    }

    svg {
        display: block;

        width: 100%;
        height: 100%;
    }
</style>
