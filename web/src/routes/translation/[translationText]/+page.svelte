<script lang="ts">
import { onMount } from "svelte";
import Graph from "$lib/components/Graph.svelte";

let {
    data,
} = $props();

let breakdownData = $state(null);

onMount(async () => {
    const breakdownResponse = await fetch(`http://localhost:5325/api/translation/${encodeURIComponent(data.translationText)}`);
    breakdownData = await breakdownResponse.json();
});

let breakdownIndex = $state(0);

let breakdown = $derived(breakdownData?.[breakdownIndex] ?? null);

let testOutline = $state("");
</script>


<div class="page">
    <div class="heading">
        <button onclick={() => breakdownIndex = breakdownIndex === 0 ? breakdownData.length - 1 : breakdownIndex - 1}>Previous</button>
        <button onclick={() => breakdownIndex = breakdownIndex === breakdownData.length - 1 ? 0 : breakdownIndex + 1}>Next</button>

        Entry {`${breakdownIndex + 1}\u2044${breakdownData?.length ?? 0}`}
    </div>

    {#if breakdown !== null}
        {breakdown.entry}
        <Graph
            data={breakdown.subtrie}
        />
    {:else}
        <div>Loading...</div>
    {/if}

    <div class="test-outline-container">
        Test outline
        <input
            type="text"
            bind:value={testOutline}
            class="test-outline"
        />
    </div>
</div>

<style lang="scss">
.page {
    width: 100vw;
    height: 100vh;

    display: flex;
    flex-direction: column;
}

.test-outline-container {
    display: flex;
    align-items: center;
    gap: 1rem;
    
    padding: 1rem;
}

.test-outline {
    flex-grow: 1;

    font-family: "Atkinson Hyperlegible Mono";
}
</style>