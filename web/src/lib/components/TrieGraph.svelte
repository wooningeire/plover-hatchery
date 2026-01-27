<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import * as d3 from "d3";

  interface TrieData {
    transitions: Record<string, number[]>[];
    translations: any[];
    keys: string[];
    node_translations: Record<string, number[]>;
    transition_costs: any[];
  }

  let { data }: { data: TrieData } = $props();

  let svgElement: SVGSVGElement;
  let width = $state(800);
  let height = $state(600);

  onMount(() => {
    width = innerWidth;
    height = innerHeight;
  });

  // Transform data for D3
  // Nodes: Just index
  // Links: source, target, label (key)
  function transformData(data: TrieData) {
    const nodes = data.transitions.map((_, i) => ({ id: i }));
    const links: any[] = [];

    // Process transition costs
    const costMap = new Map<string, number>(); // key: "src-keyId-transIdx", value: cost
    // Assuming we want to show the cost for the transition.
    // If there are multiple costs for different translations, how to aggregate?
    // Let's store all costs for a transition.
    const costsPerTransition = new Map<string, number[]>();

    data.transition_costs.forEach((item: any) => {
        const t = item.transition;
        // The transition_index likely refers to the index in the destinations array for that key?
        // Let's assume so.
        // Wait, the destinations is a list of node indices.
        // transition_index should correspond to the index in that list.
        const key = `${t.src_node_index}-${t.key_id}-${t.transition_index}`;
        if (!costsPerTransition.has(key)) {
            costsPerTransition.set(key, []);
        }
        costsPerTransition.get(key)!.push(item.cost);
    });


    data.transitions.forEach((nodeTransitions, sourceIndex) => {
      // nodeTransitions is dict[KeyId, list[int]]
      // But in JSON it might be object with string keys
      for (const [keyIdStr, destinations] of Object.entries(nodeTransitions)) {
        const keyId = parseInt(keyIdStr);
        const keyLabel = data.keys[keyId];
        
        // destinations is list[int]
        // @ts-ignore
        destinations.forEach((targetIndex: number, transitionIndex: number) => {
          const lookupKey = `${sourceIndex}-${keyId}-${transitionIndex}`;
          const costs = costsPerTransition.get(lookupKey);
          let label = keyLabel;
          if (costs && costs.length > 0) {
              // Display unique costs
              const uniqueCosts = [...new Set(costs)];
              label += ` (${uniqueCosts.join(", ")})`;
          }

          links.push({
            source: sourceIndex,
            target: targetIndex,
            label: label,
          });
        });
      }
    });

    return { nodes, links };
  }

  let simulation: d3.Simulation<any, undefined>;

  function updateGraph() {
    if (!data || !svgElement) return;

    const { nodes, links } = transformData(data);
    
    // clear previous
    d3.select(svgElement).selectAll("*").remove();

    const svg = d3.select(svgElement)
        .attr("viewBox", [-width / 2, -height / 2, width, height])
        .style("max-width", "100%")
        .style("height", "auto")
        .call(d3.zoom().on("zoom", (event) => {
            g.attr("transform", event.transform);
        }));

    const g = svg.append("g");
   
    // Arrow marker
    svg.append("defs").selectAll("marker")
      .data(["end"])
      .join("marker")
      .attr("id", "arrow")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 15)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("fill", "#999")
      .attr("d", "M0,-5L10,0L0,5");

    simulation = d3.forceSimulation(nodes)
      .force("link", d3.forceLink(links).id((d: any) => d.id).distance(125))
      .force("charge", d3.forceManyBody().strength(-2400))
      .force("x", d3.forceX())
      .force("y", d3.forceY());

    const link = g.append("g")
      .attr("fill", "none")
      .attr("stroke-width", 1.5)
      .selectAll("path")
      .data(links)
      .join("path")
      .attr("stroke", "#999")
      .attr("marker-end", "url(#arrow)");

    const linkLabel = g.append("g")
      .attr("class", "link-labels")
      .selectAll("text")
      .data(links)
      .join("text")
      .attr("font-family", "sans-serif")
      .attr("font-size", 10)
      .attr("fill", "#555")
      .attr("text-anchor", "middle")
      .text((d: any) => d.label);

    const node = g.append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll("circle")
      .data(nodes)
      .join("circle")
      .attr("r", d => {
        if (d.id === 0) {
            return 24;
        }
        
        const hasTranslation = data.node_translations[d.id] && data.node_translations[d.id].length > 0;
        if (hasTranslation) {
            return 12;
        }
        
        return 8;
      })
      .attr("fill", d => {
          const hasTranslation = data.node_translations[d.id] && data.node_translations[d.id].length > 0;
          return hasTranslation ? "#ff4444" : "#69b3a2";
      })
      .call(drag(simulation));

    node.append("title")
      .text((d) => {
           const transIds = data.node_translations[d.id] || [];
           const trans = transIds.map(id => data.translations[id]).join(", ");
           return `Node ${d.id}\n${trans}`;
      });
      
    // Add labels to nodes
    const nodeLabel = g.append("g")
        .selectAll("text")
        .data(nodes)
        .join("text")
        .attr("dx", 12)
        .attr("dy", ".35em")
        .text(d => {
            const transIds = data.node_translations[d.id];
            if (transIds && transIds.length > 0) {
                return transIds.map(id => data.translations[id]).join(", ");
            }
            return d.id;
        })
        .style("font-size", "10px")
        .style("pointer-events", "none")
        .style("user-select", "none");


    simulation.on("tick", () => {
      link.attr("d", (d: any) => {
          // Straight line
          return `M${d.source.x},${d.source.y}L${d.target.x},${d.target.y}`;
      });

      node
        .attr("cx", (d: any) => d.x)
        .attr("cy", (d: any) => d.y);
      
      linkLabel
        .attr("x", (d: any) => (d.source.x + d.target.x) / 2)
        .attr("y", (d: any) => (d.source.y + d.target.y) / 2);
    
      nodeLabel
        .attr("x", (d: any) => d.x)
        .attr("y", (d: any) => d.y);
    });
  }

  function drag(simulation: any) {
    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: any) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return d3.drag()
      .on("start", dragstarted)
      .on("drag", dragged)
      .on("end", dragended);
  }

  $effect(() => {
    if (data) {
        updateGraph();
    }
  });

</script>

<div class="graph-container">
    <svg
        bind:this={svgElement}
        {width}
        {height}
    ></svg>
</div>

<style>
    .graph-container {
        width: 100%;
        height: 100vh;
        border: 1px solid #ccc;
        overflow: hidden;
    }
</style>
