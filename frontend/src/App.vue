<template>
  <div id="app">
    <h1>Tabular Data Manager</h1>

    <div class="container">
      <h2>Datasets</h2>
      <div class="controls">
        <select v-model="selectedDataset" @change="loadDataset">
          <option value="">Select a dataset</option>
          <option v-for="(info, name) in datasets" :key="name" :value="name">
            {{ name }} ({{ info.rows }} rows)
          </option>
        </select>
        <button @click="loadDatasets">Refresh Datasets</button>
        <button class="danger" @click="deleteDataset" :disabled="!selectedDataset">
          Delete Dataset
        </button>
      </div>

      <div v-if="selectedDataset" class="dataset-info">
        <div class="info-item">
          <label>Dataset Name</label>
          <span>{{ selectedDataset }}</span>
        </div>
        <div class="info-item">
          <label>Total Rows</label>
          <span>{{ currentData?.total_rows || 0 }}</span>
        </div>
        <div class="info-item">
          <label>Columns</label>
          <span>{{ currentData?.columns?.length || 0 }}</span>
        </div>
      </div>
    </div>

    <div v-if="selectedDataset" class="container">
      <h2>Data Operations</h2>
      <div class="controls">
        <select v-model="filterColumn">
          <option value="">Select column to filter</option>
          <option v-for="col in currentData?.columns" :key="col" :value="col">
            {{ col }}
          </option>
        </select>
        <select v-model="filterOperation">
          <option value="eq">Equals</option>
          <option value="gt">Greater Than</option>
          <option value="lt">Less Than</option>
          <option value="contains">Contains</option>
        </select>
        <input v-model="filterValue" placeholder="Filter value">
        <button @click="applyFilter" :disabled="!filterColumn">Apply Filter</button>
        <button class="secondary" @click="clearFilter">Clear Filter</button>
      </div>

      <div class="controls">
        <select v-model="aggColumn">
          <option value="">Select column for aggregation</option>
          <option v-for="col in currentData?.columns" :key="col" :value="col">
            {{ col }}
          </option>
        </select>
        <select v-model="aggOperation">
          <option value="sum">Sum</option>
          <option value="mean">Mean</option>
          <option value="median">Median</option>
          <option value="count">Count</option>
          <option value="min">Min</option>
          <option value="max">Max</option>
        </select>
        <button @click="performAggregation" :disabled="!aggColumn">Calculate</button>
      </div>

      <div v-if="aggregationResult" class="stat-card">
        <h3>{{ aggOperation.toUpperCase() }} of {{ aggColumn }}</h3>
        <p>{{ aggregationResult.result }}</p>
      </div>
    </div>

    <div v-if="error" class="error">
      {{ error }}
    </div>

    <div v-if="currentData" class="container">
      <h2>Data Table</h2>
      <div style="overflow-x: auto;">
        <table>
          <thead>
            <tr>
              <th v-for="col in currentData.columns" :key="col">{{ col }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in displayData" :key="idx">
              <td v-for="col in currentData.columns" :key="col">{{ row[col] }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="selectedDataset" class="container">
      <h2>Statistics</h2>
      <button @click="loadStatistics">Load Statistics</button>
      <div v-if="statistics" class="stats-grid">
        <div v-for="(stat, col) in statistics.statistics" :key="col" class="stat-card">
          <h3>{{ col }}</h3>
          <p v-if="stat.count">Count: {{ stat.count }}</p>
          <p v-if="stat.mean">Mean: {{ stat.mean?.toFixed(2) }}</p>
          <p v-if="stat.min !== undefined">Min: {{ stat.min }}</p>
          <p v-if="stat.max !== undefined">Max: {{ stat.max }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'App',
  data() {
    return {
      datasets: {},
      selectedDataset: '',
      currentData: null,
      displayData: [],
      filterColumn: '',
      filterOperation: 'eq',
      filterValue: '',
      aggColumn: '',
      aggOperation: 'sum',
      aggregationResult: null,
      statistics: null,
      error: null,
      isFiltered: false
    }
  },
  mounted() {
    this.loadDatasets()
  },
  methods: {
    async loadDatasets() {
      try {
        const response = await axios.get('/api/datasets')
        this.datasets = response.data
        this.error = null
      } catch (err) {
        this.error = 'Failed to load datasets: ' + err.message
      }
    },
    async loadDataset() {
      if (!this.selectedDataset) return

      try {
        const response = await axios.get(`/api/datasets/${this.selectedDataset}`)
        this.currentData = response.data
        this.displayData = response.data.data
        this.isFiltered = false
        this.aggregationResult = null
        this.statistics = null
        this.error = null
      } catch (err) {
        this.error = 'Failed to load dataset: ' + err.message
      }
    },
    async applyFilter() {
      if (!this.filterColumn || !this.selectedDataset) return

      try {
        const response = await axios.post('/api/filter', {
          dataset_name: this.selectedDataset,
          column: this.filterColumn,
          operation: this.filterOperation,
          value: this.filterValue
        })
        this.displayData = response.data.data
        this.isFiltered = true
        this.error = null
      } catch (err) {
        this.error = 'Failed to apply filter: ' + err.message
      }
    },
    clearFilter() {
      this.displayData = this.currentData.data
      this.filterColumn = ''
      this.filterValue = ''
      this.isFiltered = false
    },
    async performAggregation() {
      if (!this.aggColumn || !this.selectedDataset) return

      try {
        const response = await axios.post('/api/aggregate', {
          dataset_name: this.selectedDataset,
          column: this.aggColumn,
          operation: this.aggOperation
        })
        this.aggregationResult = response.data
        this.error = null
      } catch (err) {
        this.error = 'Failed to perform aggregation: ' + err.message
      }
    },
    async loadStatistics() {
      if (!this.selectedDataset) return

      try {
        const response = await axios.get(`/api/datasets/${this.selectedDataset}/stats`)
        this.statistics = response.data
        this.error = null
      } catch (err) {
        this.error = 'Failed to load statistics: ' + err.message
      }
    },
    async deleteDataset() {
      if (!this.selectedDataset || !confirm(`Delete dataset "${this.selectedDataset}"?`)) return

      try {
        await axios.delete(`/api/datasets/${this.selectedDataset}`)
        this.selectedDataset = ''
        this.currentData = null
        this.displayData = []
        await this.loadDatasets()
        this.error = null
      } catch (err) {
        this.error = 'Failed to delete dataset: ' + err.message
      }
    }
  }
}
</script>
