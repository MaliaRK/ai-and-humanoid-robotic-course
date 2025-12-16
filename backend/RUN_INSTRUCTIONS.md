# Instructions to Run and View Collections in Qdrant Dashboard

## Prerequisites

1. **Python 3.10+** installed on your system
2. **Cohere API key** with sufficient credits
3. **Qdrant Cloud account** with API access

## Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements_simple.txt
```

## Step 2: Configure Environment Variables

Create or update your `.env` file with your credentials:

```bash
# .env file
COHERE_API_KEY=your_cohere_api_key_here
QDRANT_URL=your_qdrant_cloud_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
```

## Step 3: Verify Qdrant Connection

First, check your Qdrant connection and see existing collections:

```bash
python check_qdrant_connection.py
```

This will show you all existing collections in your Qdrant instance.

## Step 4: Create the Collection and Ingest Sample Data

Run the simple ingestion script to create the collection and add sample data:

```bash
python simple_ingest.py
```

This script will:
- Create the `ai_book_embedding` collection in Qdrant
- Generate embeddings for sample texts using Cohere
- Store the embeddings with metadata in Qdrant
- Show you that data is now available in your dashboard

## Step 5: Run Full Ingestion (Optional)

Once you've confirmed the setup works, you can run the full ingestion pipeline:

```bash
python main.py --url "https://ai-and-humanoid-robotic-course.vercel.app/" --max-depth 2
```

## Check Your Qdrant Dashboard

After running any of the scripts above, visit your Qdrant Cloud dashboard to see the collections:

1. **For Qdrant Cloud**: Visit your cloud dashboard URL (typically looks like `https://[cluster-id].[region].cloud.qdrant.io/`)
2. You should now see the `ai_book_embedding` collection with points in it
3. Click on the collection to see the stored vectors and metadata

## Troubleshooting

If you don't see the data in your dashboard:

1. **Check API Keys**: Verify your Cohere and Qdrant API keys are correct
2. **Check Quotas**: Ensure you haven't exceeded your Cohere or Qdrant free tier limits
3. **Check Network**: Verify your internet connection allows access to both services
4. **Check Logs**: Look at the console output for any error messages
5. **Retry Connection**: Sometimes connections can be intermittent

## Expected Results

After successful execution, you should see:
- A collection named `rag_embedding` in your Qdrant dashboard
- Points with vectors and metadata (text, source_url, module_name, chunk_index)
- The ability to perform vector searches in your dashboard