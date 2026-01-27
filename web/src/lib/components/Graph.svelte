<script lang="ts">
    import { onMount, untrack } from 'svelte';
    import * as d3 from 'd3';
    import FlagControls from '$lib/components/FlagControls.svelte';

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

    let { data }: { data: GraphData } = $props();

    let svg: SVGSVGElement;
    let width = $state(800);
    let height = $state(600);

    const resize = () => {
        width = innerWidth;
        height = innerHeight;
    }

    onMount(() => {
        resize();
    });
	let container: HTMLDivElement;

    // Color scale
    const colorScale = d3.scaleOrdinal(d3.schemeTableau10);

    // Flag controls state
    let flagOpacities = $state<Record<string, number>>({});
    let uniqueFlags = $state<string[]>([]);

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
                if (flagOpacities[f] === undefined) {
                    flagOpacities[f] = 1.0;
                }
            });
        });
        
        uniqueFlags = newFlags;
    });

    $effect(() => {
        if (!data || !data.nodes || !data.transitions || !svg) return;

        // Clear previous render
        d3.select(svg).selectAll("*").remove();

        // Calculate positions: Linear layout based on array order
        const nodeRadius = 25;
		const nodeSpacing = 120;
        const margin = { top: height / 2, left: 50 }; // Center vertically

        const nodes: NodeData[] = data.nodes.map((id: number, index: number) => ({ 
            id, 
            x: margin.left + index * nodeSpacing,
            y: margin.top,
            color: colorScale(id.toString())
        }));
        
        const nodeMap = new Map<number, NodeData>(nodes.map(n => [n.id, n]));

        const links: LinkData[] = data.transitions.map((t: GraphData['transitions'][number], i) => {
            // Calculate opacity for each key and filter out invisible ones
            const visibleKeyData = t.keys_costs.map(kc => {
                let keyOpacity = 1.0;
                if (kc.flags && kc.flags.length > 0) {
                    // Use minimum opacity of associated flags
                    keyOpacity = Math.min(...kc.flags.map(f => flagOpacities[f] ?? 1.0));
                }
                return { key: kc.key, cost: kc.cost, opacity: keyOpacity };
            }).filter(k => k.opacity > 0);

            if (visibleKeyData.length === 0) return null;

            // Link opacity is the maximum of its visible keys
            const linkOpacity = Math.max(...visibleKeyData.map(k => k.opacity));

            return {
                source: t.src_node_id,
                target: t.dst_node_id,
                keys: visibleKeyData.map(k => `${k.key} (${k.cost})`),
                id: `link-${i}`,
                opacity: linkOpacity
            };
        }).filter(l => l !== null) as LinkData[];

        const svgEl = d3.select(svg);
        
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 4])
            .on("zoom", (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
                g.attr("transform", event.transform.toString());
            });
            
        svgEl.call(zoom);
        
        const g = svgEl.append("g");
        const defsInG = g.append("defs"); // Original code did this

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

        // Marker
        defsInG.append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", nodeRadius + 10) // Adjustment for node radius + some spacing
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#999");

        // Links
        // Using curved lines (Bezier) with arc depending on direction
        const path = g.append("g")
            .selectAll("path")
            .data(links)
            .join("path")
            .attr("fill", "none")
            .attr("stroke", (d: LinkData) => `url(#${d.id})`)
            .attr("stroke-opacity", (d: LinkData) => d.opacity * 0.6)
            .attr("stroke-width", 4)
            .attr("marker-end", "url(#arrowhead)")
             .attr("d", (d: LinkData) => {
                const source = nodeMap.get(d.source)!;
                const target = nodeMap.get(d.target)!;
                
                const dx = target.x - source.x;
                const arcFactor = 1; 
                const h = Math.abs(dx) * arcFactor;
                const dir = dx > 0 ? -1 : 1;
                
                const cp1x = source.x + dx / 4;
                const cp1y = source.y + h * dir;
                
                const cp2x = target.x - dx / 4;
                const cp2y = target.y + h * dir;
                
                return `M${source.x},${source.y} C${cp1x},${cp1y} ${cp2x},${cp2y} ${target.x},${target.y}`;
            });
            
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
                 const arcFactor = 1;
                 const h = Math.abs(dx) * arcFactor;
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
            .attr("stroke-width", 8);
            
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

<FlagControls flags={uniqueFlags} bind:opacities={flagOpacities} />

<div bind:this={container} class="graph-container">
    <svg bind:this={svg} {width} {height} viewBox="0 0 {width} {height}"></svg>
</div>

<style>
    .graph-container {
        border: 1px solid #ccc;
        border-radius: 4px;
        overflow: hidden;
    }
</style>
