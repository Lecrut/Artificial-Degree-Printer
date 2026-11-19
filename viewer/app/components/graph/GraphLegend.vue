<script setup lang="ts">
import { BAG_COLOR, roleColor } from '#shared/utils/roles'
import { vertexStateColor } from '#shared/utils/states'
import { labels } from '~/utils/labels'

const STATES = ['spec', 'stub', 'impl', 'written', 'drafted', 'verified', 'stale', 'failed']
const BAGS = Object.entries(BAG_COLOR).map(([type, color]) => ({ type, color }))
const ROLES = ['P', 'C', 'T', 'O', 'X']
</script>

<template>
  <div class="d-flex flex-wrap align-center ga-2">
    <span class="text-caption text-medium-emphasis me-1">{{ labels.graph.states }}</span>
    <v-chip v-for="state in STATES" :key="state" :color="vertexStateColor(state)" variant="outlined">{{ state }}</v-chip>
    <span class="text-caption text-medium-emphasis ms-4 me-1">{{ labels.graph.bags }}</span>
    <v-chip v-for="bag in BAGS" :key="bag.type" :color="bag.color" variant="flat">{{ bag.type }} · {{ labels.graph.bagNames[bag.type] }}</v-chip>
    <span class="text-caption text-medium-emphasis ms-4 me-1">{{ labels.graph.roles }}</span>
    <v-chip v-for="role in ROLES" :key="role" :color="roleColor(role)" size="x-small" variant="flat">{{ role }} · {{ labels.graph.roleNames[role] }}</v-chip>
  </div>
</template>
