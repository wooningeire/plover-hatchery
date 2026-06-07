<script lang="ts">
import { onMount } from "svelte";
import Graph from "$lib/components/Graph.svelte";
import {
    loadLookupBreakdown,
    loadTranslationBreakdown,
    type TranslationBreakdown,
} from "$lib/ploverApi";

type PageData = {
    translationText: string;
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
let timeoutId: ReturnType<typeof setTimeout> | null = null;

onMount(async () => {
    translationBreakdownIsLoading = true;
    translationBreakdownError = null;

    try {
        translationBreakdownData = await loadTranslationBreakdown(data.translationText);
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

    if (timeoutId !== null) {
        clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(async () => {
        try {
            lookupBreakdownData = await loadLookupBreakdown(testOutline);
        } catch (error) {
            lookupBreakdownData = null;
            translationBreakdownError = error instanceof Error ? error.message : String(error);
        }
    }, 50);

    return () => {
        if (timeoutId !== null) {
            clearTimeout(timeoutId);
        }
    };
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
