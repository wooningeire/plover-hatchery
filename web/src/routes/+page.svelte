<script lang="ts">
import { onMount } from "svelte";
import TrieGraph from "$lib/components/TrieGraph.svelte";

let trieData = $state(null);

onMount(async () => {
    const response = await fetch("http://localhost:5325/trie");
    trieData = await response.json();
    console.log(trieData);
});
</script>

{#if trieData !== null}
    <TrieGraph data={trieData} />
{:else}
    <p>Loading...</p>
{/if}