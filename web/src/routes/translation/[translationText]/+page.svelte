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
</script>

{#if breakdownData !== null}
    <Graph data={breakdownData} />
{:else}
    <p>Loading...</p>
{/if}