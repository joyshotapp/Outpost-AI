output "endpoint" { value = aws_elasticache_cluster.main.cache_nodes[0].address }
output "port" { value = aws_elasticache_cluster.main.port }
output "cluster_id" { value = aws_elasticache_cluster.main.cluster_id }
