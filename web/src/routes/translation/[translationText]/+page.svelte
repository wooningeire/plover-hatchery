<script lang="ts">
import { onMount } from "svelte";

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
    <pre>{JSON.stringify(breakdownData, null, 2)}</pre>
{:else}
    <p>Loading...</p>
{/if}