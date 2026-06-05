<script lang="ts">
import { onMount } from "svelte";
import Graph from "$lib/components/Graph.svelte";

type PageData = {
    translationText: string;
};

type TranslationBreakdown = {
    entry: string;
    subtrie: any;
};

let {
    data,
}: {
    data: PageData,
} = $props();

let translationBreakdownData = $state<TranslationBreakdown[]>([]);
let translationBreakdownError = $state<string | null>(null);
let translationBreakdownIsLoading = $state(true);
let breakdownIndex = $state(0);

let breakdown = $derived(translationBreakdownData[breakdownIndex] ?? null);
let breakdownCount = $derived(translationBreakdownData.length);

let testOutline = $state("");
let lookupBreakdownData = $state<any[] | null>(null);
let timeoutId = 0;

onMount(async () => {
    translationBreakdownIsLoading = true;
    translationBreakdownError = null;

    try {
        const response = await fetch(`http://localhost:5325/api/breakdown_translation/${encodeURIComponent(data.translationText)}`);
        const responseData = await response.json();
        translationBreakdownData = Array.isArray(responseData) ? responseData : [];
        breakdownIndex = 0;
    } catch (error) {
        translationBreakdownError = error instanceof Error ? error.message : String(error);
    } finally {
        translationBreakdownIsLoading = false;
    }
});

function previousBreakdown() {
    if (breakdownCount === 0) {
        return;
    }

    breakdownIndex = breakdownIndex === 0 ? breakdownCount - 1 : breakdownIndex - 1;
}

function nextBreakdown() {
    if (breakdownCount === 0) {
        return;
    }

    breakdownIndex = breakdownIndex === breakdownCount - 1 ? 0 : breakdownIndex + 1;
}

$effect(() => {
    if (testOutline === "") {
        lookupBreakdownData = null;
        return;
    }

    clearTimeout(timeoutId);

    timeoutId = setTimeout(async () => {
        const lookupBreakdownResponse = await fetch(`http://localhost:5325/api/breakdown_lookup/${encodeURIComponent(testOutline.replaceAll("/", " "))}`);
        lookupBreakdownData = await lookupBreakdownResponse.json();
    }, 50);
});
</script>


<div class="page">
    <div class="entry-controls">
        <button disabled={breakdownCount === 0} onclick={previousBreakdown}>Previous</button>
        <button disabled={breakdownCount === 0} onclick={nextBreakdown}>Next</button>

        <div class="entry-number">
            Entry <sup>{breakdownIndex + 1}</sup>&#x2044;<sub>{breakdownCount}</sub>
        </div>
        
        {breakdown?.entry}
    </div>

    {#if translationBreakdownIsLoading}
        <div>Loading...</div>
    {:else if translationBreakdownError !== null}
        <div>Failed to load breakdown for "{data.translationText}": {translationBreakdownError}</div>
    {:else if breakdown !== null}
        <Graph
            data={breakdown.subtrie}
            highlightData={lookupBreakdownData}
        />
    {:else}
        <div>No breakdown found for "{data.translationText}"</div>
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
