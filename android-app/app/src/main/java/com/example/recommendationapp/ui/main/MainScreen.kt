package com.example.recommendationapp.ui.main

import android.util.Log
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import androidx.navigation3.runtime.NavKey

data class AnimeRec(val title: String, val score: Double)

@Composable
fun MainScreen(onItemClick: (NavKey) -> Unit, modifier: Modifier = Modifier) {
    var query by remember { mutableStateOf("1") }
    var results by remember { mutableStateOf<List<AnimeRec>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    val coroutineScope = rememberCoroutineScope()

    Column(modifier = modifier.padding(16.dp).fillMaxSize()) {
        Text("Anime Recommender", style = MaterialTheme.typography.headlineMedium)
        Spacer(modifier = Modifier.height(16.dp))
        
        OutlinedTextField(
            value = query,
            onValueChange = { query = it },
            label = { Text("Enter Anime MAL ID (e.g. 1)") },
            modifier = Modifier.fillMaxWidth()
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Button(
            onClick = {
                isLoading = true
                errorMessage = null
                
                coroutineScope.launch(Dispatchers.IO) {
                    try {
                        val url = URL("http://10.0.2.2:8000/anime/${query}/recommend?n=5")
                        val connection = url.openConnection() as HttpURLConnection
                        connection.requestMethod = "GET"
                        connection.connectTimeout = 5000
                        connection.readTimeout = 5000
                        
                        if (connection.responseCode == 200) {
                            val response = connection.inputStream.bufferedReader().use { it.readText() }
                            val jsonObject = JSONObject(response)
                            val recsArray = jsonObject.getJSONArray("recommendations")
                            
                            val fetchedRecs = mutableListOf<AnimeRec>()
                            for (i in 0 until recsArray.length()) {
                                val item = recsArray.getJSONObject(i)
                                fetchedRecs.add(AnimeRec(
                                    title = item.getString("title"),
                                    score = item.getDouble("similarity_score")
                                ))
                            }
                            
                            withContext(Dispatchers.Main) {
                                results = fetchedRecs
                                isLoading = false
                            }
                        } else {
                            withContext(Dispatchers.Main) {
                                errorMessage = "HTTP Error: ${connection.responseCode}"
                                isLoading = false
                            }
                        }
                    } catch (e: Exception) {
                        Log.e("MainScreen", "Network error", e)
                        withContext(Dispatchers.Main) {
                            errorMessage = e.message ?: "Unknown error"
                            isLoading = false
                        }
                    }
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Get Recommendations")
        }
        
        Spacer(modifier = Modifier.height(16.dp))
        
        if (isLoading) {
            CircularProgressIndicator()
        } else if (errorMessage != null) {
            Text("Error: $errorMessage", color = MaterialTheme.colorScheme.error)
        } else {
            LazyColumn {
                items(results) { rec ->
                    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
                        Column(modifier = Modifier.padding(16.dp)) {
                            Text(rec.title, style = MaterialTheme.typography.titleMedium)
                            Text("Similarity Score: ${rec.score}", style = MaterialTheme.typography.bodyMedium)
                        }
                    }
                }
            }
        }
    }
}
