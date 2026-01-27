<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import * as d3 from 'd3';

    interface NodeData {
        id: number;
        x: number;
        y: number;
        color: string;
    }

    interface LinkData {
        source: number;
        target: number;
        keys: string;
        id: string;
    }

    interface GraphData {
        nodes: number[];
        transitions: {
            src_node_id: number;
            dst_node_id: number;
            keys: string[];
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

    $effect(() => {
        if (!data || !data.nodes || !data.transitions || !svg) return;

        // Clear previous render
        d3.select(svg).selectAll("*").remove();

        // Calculate positions: Linear layout based on array order
        const nodeRadius = 20;
		const nodeSpacing = 100;
        const margin = { top: height / 2, left: 50 }; // Center vertically

        const nodes: NodeData[] = data.nodes.map((id: number, index: number) => ({ 
            id, 
            x: margin.left + index * nodeSpacing,
            y: margin.top,
            color: colorScale(id.toString())
        }));
        
        const nodeMap = new Map<number, NodeData>(nodes.map(n => [n.id, n]));

        const links: LinkData[] = data.transitions.map((t: {src_node_id: number, dst_node_id: number, keys: string[]}, i) => ({
            source: t.src_node_id,
            target: t.dst_node_id,
            keys: t.keys.join(", "),
            id: `link-${i}`
        }));

        const svgEl = d3.select(svg);
        
        const zoom = d3.zoom<SVGSVGElement, unknown>()
            .scaleExtent([0.1, 4])
            .on("zoom", (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
                g.attr("transform", event.transform.toString());
            });
            
        svgEl.call(zoom);
        
        const g = svgEl.append("g");
        
        const defs = g.append("defs");

        // Arrow marker (keep generic for now)
        defs.append("marker")
            .attr("id", "arrowhead")
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", nodeRadius + 5) // node radius + padding
            .attr("refY", 0)
            .attr("markerWidth", 6)
            .attr("markerHeight", 6)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#555");
            
        // Gradients for links
        links.forEach(link => {
            const source = nodeMap.get(link.source)!;
            const target = nodeMap.get(link.target)!;
            
            const gradient = defs.append("linearGradient")
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
        g.append("g")
            .selectAll("path")
            .data(links)
            .join("path")
            .attr("fill", "none")
            .attr("stroke", d => `url(#${d.id})`)
            .attr("stroke-opacity", 0.5)
            .attr("stroke-width", 2)
            .attr("marker-end", "url(#arrowhead)")
             .attr("d", (d: LinkData) => {
                const source = nodeMap.get(d.source)!;
                const target = nodeMap.get(d.target)!;
                
                const dx = target.x - source.x;
                // Arc height proportional to distance
                // If forward (dx > 0), arc up (negative Y offset)
                // If backward (dx < 0), arc down (positive Y offset)
                const arcFactor = 1.25; // Adjust for curvature
                const h = Math.abs(dx) * arcFactor;
                const dir = dx > 0 ? -1 : 1;
                
                const cp1x = source.x + dx / 4;
                const cp1y = source.y;
                
                const cp2x = target.x;
                const cp2y = target.y + h * dir;
                
                return `M${source.x},${source.y} C${cp1x},${cp1y} ${cp2x},${cp2y} ${target.x},${target.y}`;
            });
            
        // Link Labels
        g.append("g")
            .selectAll("text")
            .data(links)
            .join("text")
            .attr("font-family", "sans-serif")
            .attr("font-size", 10)
            .attr("fill", "#333")
            .attr("text-anchor", "middle")
             .attr("x", (d: LinkData) => {
                 const source = nodeMap.get(d.source)!;
                 const target = nodeMap.get(d.target)!;
                 return source.x * 1/4 + target.x * 3/4 ;
             })
             .attr("y", (d: LinkData) => {
                 const source = nodeMap.get(d.source)!;
                 const target = nodeMap.get(d.target)!;
                 const dx = target.x - source.x;
                 const dir = dx > 0 ? -1 : 1;
                 // Position label at the peak of the arc
                 // approximate peak Y
                 const arcFactor = 1;
                 const h = Math.abs(dx) * arcFactor;
                 return source.y + (h * dir * 0.5); 
             })
             .style("background-color", "rgba(255, 255, 255, 0.8)") // SVG doesn't support generic bg color on text elements
             .each(function() {
                 // Optional: Add a white rect background if needed for readability
             })
            .text((d: LinkData) => d.keys);


        // Nodes
        const nodeGroups = g.append("g")
            .selectAll("g")
            .data(nodes)
            .join("g")
            .attr("transform", (d: NodeData) => `translate(${d.x},${d.y})`);

        nodeGroups.append("circle")
            .attr("r", nodeRadius)
            .attr("fill", d => d.color)
            .attr("stroke", d => d.color)
            .attr("stroke-opacity", 0.5)
            .attr("stroke-width", 8);

        nodeGroups.append("text")
            .attr("dy", "0.35em")
            .attr("text-anchor", "middle")
            .attr("fill", "white") // White text on colored background usually works better
            .attr("font-family", "sans-serif")
            .attr("font-size", 14)
            .attr("font-weight", "bold")
            .style("pointer-events", "none") // Let clicks pass through to circle if needed
            .text((d: NodeData) => d.id.toString());
    });
</script>

<svelte:window onresize={resize} />

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
