<script lang="ts">
import { onMount } from "svelte";

onMount(async () => {
    const response = await fetch("http://localhost:5325/?translation=hello");
    console.log(await response.json());
});
</script>

<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>
