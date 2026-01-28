<script lang="ts">
import { onMount } from "svelte";
import Graph from "$lib/components/Graph.svelte";

let {
    data,
} = $props();

let breakdownData = $state(null);

onMount(async () => {
    const breakdownResponse = await fetch(`http://localhost:5325/?translation=${encodeURIComponent(data.translationText)}`);
    breakdownData = await breakdownResponse.json();
});

let breakdownIndex = $state(0);

let breakdown = $derived(breakdownData?.[breakdownIndex] ?? null);
</script>


<button onclick={() => breakdownIndex = breakdownIndex === 0 ? breakdownData.length - 1 : breakdownIndex - 1}>Previous</button>
<button onclick={() => breakdownIndex = breakdownIndex === breakdownData.length - 1 ? 0 : breakdownIndex + 1}>Next</button>

Entry {`${breakdownIndex + 1}\u2044${breakdownData?.length ?? 0}`}

{#if breakdown !== null}
    {breakdown.entry}
    <Graph
        data={breakdown.subtrie}
    />
{:else}
    <p>Loading...</p>
{/if}