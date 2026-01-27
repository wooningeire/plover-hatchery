<script lang="ts">
import { onMount } from "svelte";


onMount(async () => {
    const response = await fetch("http://localhost:5325/trie");
    console.log(await response.json());
});
</script>