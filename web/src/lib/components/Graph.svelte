<script lang="ts">
    import { onMount, untrack } from 'svelte';
    import * as d3 from 'd3';
    import FlagControls, { type FlagSettings } from '$lib/components/FlagControls.svelte';

    interface NodeData {
        id: number;
        x: number;
        y: number;
        color: string;
    }

    interface LinkData {
        source: number;
        target: number;
        keys: string[];
        id: string;
        opacity: number;
        strokeWidth: number;
        dashArray: string | null;
    }

    interface GraphData {
        nodes: number[];
        transitions: {
            src_node_id: number;
            dst_node_id: number;
            keys_costs: {
                key: string;
                cost: number;
                flags?: string[];
            }[];
        }[];
    }

    interface BreakdownPathStep {
        sophs: string[];
        chord: string;
        nodes: number[]; // [source, target]
    }

    interface BreakdownPath {
        path: BreakdownPathStep[];
    }

    let {
        data,
        highlightData = null,
    }: {
        data: GraphData,
        highlightData?: BreakdownPath[] | null,
    } = $props();

    const translationNodesSet = $derived(new Set(data.translation_nodes));

    let svg: SVGSVGElement;
    let width = $state(800);
    let height = $state(600);

    let mainGroup: d3.Selection<SVGGElement, unknown, null, undefined>;

    const resize = () => {
        width = innerWidth;
        height = innerHeight;
    }

    onMount(() => {
        resize();
        if (svg) {
             const svgEl = d3.select(svg);
             const g = svgEl.append("g");
             mainGroup = g;

            const zoom = d3.zoom<SVGSVGElement, unknown>()
                .scaleExtent([0.1, 4])
                .on("zoom", (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
                    g.attr("transform", event.transform.toString());
                });
                
            svgEl.call(zoom);
        }
    });
	let container: HTMLDivElement;

    // Color scale
    const colorScale = d3.scaleOrdinal(d3.schemeTableau10);

    // Flag controls state
    const UNFLAGGED_KEY = '(unflagged)';
    const LOCAL_STORAGE_KEY = 'flagControlsSettings';
    const DEFAULT_FLAG_SETTINGS: FlagSettings = { opacity: 1.0, strokeWidth: 4, dashed: false, dashLength: 5 };
    
    // Load initial settings from localStorage
    function loadFlagSettings(): Record<string, FlagSettings> {
        try {
            const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
            if (stored) {
                const parsed = JSON.parse(stored);
                // Ensure unflagged key exists
                if (!parsed[UNFLAGGED_KEY]) {
                    parsed[UNFLAGGED_KEY] = { ...DEFAULT_FLAG_SETTINGS };
                }
                return parsed;
            }
        } catch (e) {
            console.warn('Failed to load flag settings from localStorage:', e);
        }
        return { [UNFLAGGED_KEY]: { ...DEFAULT_FLAG_SETTINGS } };
    }
    
    let flagSettings = $state<Record<string, FlagSettings>>(loadFlagSettings());
    let uniqueFlags = $state<string[]>([]);
    
    // Save settings to localStorage whenever they change
    $effect(() => {
        // Access flagSettings to create dependency
        const settingsSnapshot = JSON.stringify(flagSettings);
        try {
            localStorage.setItem(LOCAL_STORAGE_KEY, settingsSnapshot);
        } catch (e) {
            console.warn('Failed to save flag settings to localStorage:', e);
        }
    });

    $effect(() => {
        if (!data || !data.transitions) return;
        
        const flags = new Set<string>();
        data.transitions.forEach(t => {
            t.keys_costs.forEach(kc => {
                if (kc.flags) {
                    kc.flags.forEach(f => flags.add(f));
                }
            });
        });
        
        const newFlags = Array.from(flags).sort();
        
        untrack(() => {
            newFlags.forEach(f => {
                if (flagSettings[f] === undefined) {
                    flagSettings[f] = { ...DEFAULT_FLAG_SETTINGS };
                }
            });
        });
        
        uniqueFlags = [UNFLAGGED_KEY, ...newFlags];
    });

    $effect(() => {
        if (!data || !data.nodes || !data.transitions || !svg || !mainGroup) return;

        // Clear previous render content only within the main group
        mainGroup.selectAll("*").remove();

        // Calculate positions: Linear layout based on array order
        const nodeRadius = 25;
		const nodeSpacing = 200;
        const margin = { top: height / 2, left: 50 }; // Center vertically
        const arc = 0.5;

        const nodes: NodeData[] = data.nodes.map((id: number, index: number) => ({ 
            id, 
            x: margin.left + index * nodeSpacing,
            y: margin.top,
            color: colorScale(id.toString())
        }));
        
        const nodeMap = new Map<number, NodeData>(nodes.map(n => [n.id, n]));

        const links: LinkData[] = data.transitions.map((t: GraphData['transitions'][number], i) => {
            // Calculate opacity and dash settings for each key
            const visibleKeyData = t.keys_costs.map(kc => {
                let keyOpacity = 1.0;
                let keyStrokeWidth = 4;
                let keyDashed = false;
                let keyDashLength = 5;
                
                if (kc.flags && kc.flags.length > 0) {
                    // Use minimum opacity of associated flags
                    keyOpacity = Math.min(...kc.flags.map(f => flagSettings[f]?.opacity ?? 1.0));
                    // Use max stroke width
                    keyStrokeWidth = Math.max(...kc.flags.map(f => flagSettings[f]?.strokeWidth ?? 4));
                    // If any flag is dashed, the key is dashed
                    keyDashed = kc.flags.some(f => flagSettings[f]?.dashed ?? false);
                    // Use max dash length if dashed
                    if (keyDashed) {
                        keyDashLength = Math.max(...kc.flags.filter(f => flagSettings[f]?.dashed).map(f => flagSettings[f]?.dashLength ?? 5));
                    }
                } else {
                    // No flags - use unflagged settings
                    const unflagged = flagSettings[UNFLAGGED_KEY];
                    if (unflagged) {
                        keyOpacity = unflagged.opacity;
                        keyStrokeWidth = unflagged.strokeWidth;
                        keyDashed = unflagged.dashed;
                        keyDashLength = unflagged.dashLength;
                    }
                }
                return { key: kc.key, cost: kc.cost, opacity: keyOpacity, strokeWidth: keyStrokeWidth, dashed: keyDashed, dashLength: keyDashLength };
            }).filter(k => k.opacity > 0);

            if (visibleKeyData.length === 0) return null;

            // Link opacity is the maximum of its visible keys
            const linkOpacity = Math.max(...visibleKeyData.map(k => k.opacity));
            
            // Link stroke width is the maximum of its visible keys
            const linkStrokeWidth = Math.max(...visibleKeyData.map(k => k.strokeWidth));
            
            // Link is dashed if any visible key is dashed. Use max dash length.
            const isDashed = visibleKeyData.some(k => k.dashed);
            const dashLength = isDashed ? Math.max(...visibleKeyData.filter(k => k.dashed).map(k => k.dashLength)) : 0;
            const dashArray = isDashed ? `${dashLength},${dashLength * 0.5}` : null;

            return {
                source: t.src_node_id,
                target: t.dst_node_id,
                keys: visibleKeyData.map(k => `${k.key} (${k.cost})`),
                id: `link-${i}`,
                opacity: linkOpacity,
                strokeWidth: linkStrokeWidth,
                dashArray
            };
        }).filter(l => l !== null) as LinkData[];

        // Use the main group for content
        const g = mainGroup;
        const defsInG = g.append("defs");

        // Gradients for links
        links.forEach(link => {
            const source = nodeMap.get(link.source)!;
            const target = nodeMap.get(link.target)!;
            
            const gradient = defsInG.append("linearGradient")
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

        // Links
        // Using curved lines (Bezier) with arc depending on direction
        const path = g.append("g")
            .selectAll("path")
            .data(links)
            .join("path")
            .attr("fill", "none")
            .attr("stroke", (d: LinkData) => `url(#${d.id})`)
            .attr("stroke-opacity", (d: LinkData) => d.opacity * 0.6)
            .attr("stroke-width", (d: LinkData) => d.strokeWidth)
            .attr("stroke-dasharray", (d: LinkData) => d.dashArray)
             .attr("d", (d: LinkData) => {
                const source = nodeMap.get(d.source)!;
                const target = nodeMap.get(d.target)!;
                
                const dx = target.x - source.x;
                const h = Math.abs(dx) * arc;
                const dir = dx > 0 ? -1 : 1;
                
                const cp1x = source.x + dx / 4;
                const cp1y = source.y + h * dir;
                
                const cp2x = target.x - dx / 4;
                const cp2y = target.y + h * dir;
                
                return `M${source.x},${source.y} C${cp1x},${cp1y} ${cp2x},${cp2y} ${target.x},${target.y}`;
            });

        // Highlights for lookup path
        const highlightedNodes = new Set<number>();
        const highlightedLinks: { source: number, target: number, chord: string }[] = [];
        const highlightedLinkKeys = new Set<string>();

        if (highlightData) {
            pathLoop:
            for (const pathData of highlightData) {
                const links: { source: number, target: number, chord: string }[] = [];
                const nodes = new Set<number>();
                for (const step of pathData.path) {
                    if (step.nodes && step.nodes.length >= 2) {
                        for (let i = 0; i < step.nodes.length - 1; i++) {
                            const source = step.nodes[i];
                            const target = step.nodes[i + 1];

                            if (!nodeMap.has(source) || !nodeMap.has(target)) continue pathLoop;

                            links.push({ source, target, chord: i === 0 ? step.chord : "..." });
                            nodes.add(source);
                            nodes.add(target);
                        }
                    }
                }

                links.forEach(link => {
                    const key = `${link.source}-${link.target}`;
                    if (!highlightedLinkKeys.has(key)) {
                        highlightedLinkKeys.add(key);
                        highlightedLinks.push(link);
                    }
                });
                for (const node of nodes.values()) {
                    highlightedNodes.add(node);
                }
            }
        }

        const highlightGroup = g.append("g").attr("class", "highlights");

        // Highlight Links
        highlightGroup.selectAll("path")
            .data(highlightedLinks)
            .join("path")
            .attr("fill", "none")
            .attr("stroke", "red")
            .attr("stroke-width", 6)
            .attr("stroke-opacity", 0.8)
            .attr("d", d => {
                const source = nodeMap.get(d.source);
                const target = nodeMap.get(d.target);
                
                if (!source || !target) return "";

                const dx = target.x - source.x;
                const h = Math.abs(dx) * arc;
                const dir = dx > 0 ? -1 : 1;
                
                const cp1x = source.x + dx / 4;
                const cp1y = source.y + h * dir;
                
                const cp2x = target.x - dx / 4;
                const cp2y = target.y + h * dir;
                
                return `M${source.x},${source.y} C${cp1x},${cp1y} ${cp2x},${cp2y} ${target.x},${target.y}`;
            });

        // Highlight Link Labels (Chord)
        highlightGroup.selectAll("text")
            .data(highlightedLinks)
            .join("text")
            .attr("font-family", "Atkinson Hyperlegible Next")
            .attr("fill", "red")
            .attr("font-weight", "bold")
            .attr("text-anchor", "middle")
            .attr("x", d => {
                const source = nodeMap.get(d.source);
                const target = nodeMap.get(d.target);
                return source && target ? (source.x + target.x) / 2 : 0;
            })
            .attr("y", d => {
                const source = nodeMap.get(d.source);
                const target = nodeMap.get(d.target);
                if (!source || !target) return 0;
                
                const dx = target.x - source.x;
                const dir = dx > 0 ? -1 : 1;
                const h = Math.abs(dx) * arc;
                // Position slightly above the path's midpoint
                return source.y + h * dir * 0.8 - 15; 
            })
            .style("font-size", "2rem")
            .style("background-color", "rgba(255, 255, 255, 0.9)")
             // Add a small background rect for readability if needed, or text-shadow
            .style("text-shadow", "0px 0px 4px white")
            .text(d => d.chord);

            
        // Link Labels
        g.append("g")
            .selectAll("text")
            .data(links)
            .join("text")
            .attr("font-family", "Atkinson Hyperlegible Next")
            .attr("font-size", 16)
            .attr("fill", "#333")
            .attr("font-weight", "normal")
            .attr("text-anchor", "middle")
             .attr("x", (d: LinkData) => {
                 const source = nodeMap.get(d.source)!;
                 const target = nodeMap.get(d.target)!;
                 return (source.x + target.x) / 2;
             })
             .attr("y", (d: LinkData) => {
                 const source = nodeMap.get(d.source)!;
                 const target = nodeMap.get(d.target)!;
                 const dx = target.x - source.x;
                 const dir = dx > 0 ? -1 : 1;
                 const h = Math.abs(dx) * arc;
                 return source.y + h * dir * 0.72; 
             })
             .style("background-color", "rgba(255, 255, 255, 0.8)") 
             .style("opacity", (d: LinkData) => d.opacity)
            .text((d: LinkData) => d.keys.join(", "));


        // Nodes
        const nodeGroups = g.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("transform", (d: NodeData) => `translate(${d.x},${d.y})`);

        nodeGroups.append("circle")
            .attr("r", nodeRadius)
            .attr("fill", (d: NodeData) => d.color)
            .attr("stroke", (d: NodeData) => d.color)
            .attr("stroke-opacity", 0.5)
            .attr("stroke-width", (d: NodeData) => translationNodesSet.has(d.id) ? 36 : 0);
        
        
        nodeGroups.append("circle")
            .filter((d: NodeData) =>highlightedNodes.has(d.id))
            .attr("r", nodeRadius)
            .attr("fill", "none")
            .attr("stroke", "#f00")
            .attr("stroke-opacity", 0.8)
            .attr("stroke-width", 6);
    

            
         // Node labels (ID)
         nodeGroups.append("text")
            .attr("dy", 5)
            .attr("text-anchor", "middle")
            .attr("fill", "white")
            .attr("font-family", "sans-serif")
            .attr("font-weight", "bold")
            .text((d: NodeData) => d.id);
    });
</script>

<svelte:window onresize={resize} />

<FlagControls flags={uniqueFlags} bind:settings={flagSettings} />

<div
    bind:this={container}
    bind:clientWidth={() => null!, containerWidth => width = containerWidth}
    bind:clientHeight={() => null!, containerHeight => height = containerHeight}
    class="graph-container"
>
    <svg bind:this={svg} {width} {height} viewBox="0 0 {width} {height}"></svg>
</div>

<style>
.graph-container {
    overflow: hidden;

    background-color: oklch(0.98 0.003 150);
    border-radius: 4px;
}
</style>
