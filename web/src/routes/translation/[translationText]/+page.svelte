<script lang="ts">
import { onMount } from "svelte";
import Graph from "$lib/components/Graph.svelte";

let {
    data,
} = $props();

let translationBreakdownData = $state(null);

const translationBreakdownPromise = fetch(`http://localhost:5325/api/breakdown_translation/${encodeURIComponent(data.translationText)}`);
onMount(async () => {
    const translationBreakdownResponse = await translationBreakdownPromise;
    translationBreakdownData = await translationBreakdownResponse.json();
});

let breakdownIndex = $state(0);

let breakdown = $derived(translationBreakdownData?.[breakdownIndex] ?? null);

let testOutline = $state("");
let lookupBreakdownData = $state(null);
let timeoutId = 0;
$effect(() => {
    if (testOutline === "") {
        lookupBreakdownData = null;
        return;
    }

    clearTimeout(timeoutId);

    timeoutId = setTimeout(async () => {
        const lookupBreakdownResponse = await fetch(`http://localhost:5325/api/breakdown_lookup/${encodeURIComponent(testOutline.replaceAll("/", " "))}`);
        lookupBreakdownData = await lookupBreakdownResponse.json();
        console.log(lookupBreakdownData);
    }, 250);
});
</script>


<div class="page">
    <div class="entry-controls">
        <button onclick={() => breakdownIndex = breakdownIndex === 0 ? translationBreakdownData.length - 1 : breakdownIndex - 1}>Previous</button>
        <button onclick={() => breakdownIndex = breakdownIndex === translationBreakdownData.length - 1 ? 0 : breakdownIndex + 1}>Next</button>

        <div class="entry-number">
            Entry <sup>{breakdownIndex + 1}</sup>&#x2044;<sub>{translationBreakdownData?.length ?? 0}</sub>
        </div>
        
        {breakdown?.entry}
    </div>

    {#await translationBreakdownPromise}
        <div>Loading...</div>
    {:then _}
        {#if breakdown !== null}
            <Graph
                data={breakdown.subtrie}
                highlightData={lookupBreakdownData}
            />
        {:else}
            <div>No breakdown found for "{data.translationText}"</div>
        {/if}
    {:catch error}
        <div>Failed to load breakdown for "{data.translationText}": {error}</div>
    {/await}

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

.entry-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
    
    padding: 1rem;
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