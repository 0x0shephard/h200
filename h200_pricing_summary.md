# H200 GPU Pricing Summary

Data collected on: 2026-01-02

## All Cloud Providers - H200 Pricing Comparison

| Provider | Price per GPU/hour | Source |
|----------|-------------------|--------|
| **Vultr** | **$1.99/hr** | https://www.vultr.com/pricing/ |
| **Vast.ai** | **$2.19/hr** | https://vast.ai/pricing |
| **Sesterce** | **$2.25/hr** | https://www.sesterce.com/pricing |
| **FluidStack** | **$2.30/hr** | https://www.fluidstack.io/resources/pricing |
| **Nebius** | **$2.30/hr** | https://nebius.com/prices |
| **HyperStack Cloud** | **$3.50/hr** | https://www.hyperstack.cloud/gpu-pricing |
| **RunPod** | **$3.59/hr** | https://www.runpod.io/pricing |
| **JarvisLabs** | **$3.80/hr** | https://jarvislabs.ai/pricing |
| **CoreWeave** | **$6.50/hr** | https://www.coreweave.com/pricing |
| AWS (P5en.48xlarge) | $7.91/hr | https://aws.amazon.com/ec2/pricing/on-demand/ |
| Oracle Cloud (BM.GPU.H200.8) | $10.00/hr | https://www.oracle.com/cloud/compute/pricing/ |
| GCP (A3-Ultra) | $10.85/hr | https://cloud.google.com/compute/gpus-pricing |
| Azure (ND96isr_H200_v5) | $13.09/hr | https://azure.microsoft.com/pricing/details/virtual-machines/linux/ |

## Key Findings

### Most Affordable Providers (Specialized GPU Cloud)
1. **Vultr**: $1.99/hr - Best overall value for H200 GPUs
2. **Vast.ai**: $2.19/hr - Excellent spot/on-demand pricing
3. **Sesterce**: $2.25/hr - Very competitive pricing
4. **FluidStack**: $2.30/hr - Tied with Nebius for 4th place
5. **Nebius**: $2.30/hr - Tied with FluidStack for 4th place
6. **HyperStack Cloud**: $3.50/hr - Still 56% cheaper than AWS
7. **RunPod**: $3.59/hr - Competitive pricing
8. **JarvisLabs**: $3.80/hr - Good value with table pricing
9. **CoreWeave**: $6.50/hr - Mid-range specialized provider

### Major Cloud Providers
- **AWS**: $7.91/hr (P5en.48xlarge instances with 8x H200)
- **Oracle**: $10.00/hr (BM.GPU.H200.8 bare metal with 8x H200)
- **GCP**: $10.85/hr (A3-Ultra instances with 8x H200)
- **Azure**: $13.09/hr (ND96isr_H200_v5 instances with 8x H200)

### Providers Without H200 Pricing
- **Genesis Cloud**: H200 pricing not found on their pricing page
- **Gcore**: H200 mentioned but no specific pricing available
- May not have H200 GPUs available yet or pricing requires custom quote

## GPU Specifications
- **Model**: NVIDIA H200
- **Memory**: 141GB HBM3e
- **Typical deployment**: 8 GPUs per instance (major cloud providers)

## Cost Savings Analysis

**Specialized providers offer 75-85% cost savings vs major cloud providers:**
- Vultr ($1.99/hr) is **85% cheaper** than Azure ($13.09/hr)
- Vultr ($1.99/hr) is **75% cheaper** than AWS ($7.91/hr)
- Average specialized provider price: **$2.78/hr**
- Average major cloud provider price: **$10.46/hr**
- **Average savings: 73%** by using specialized providers

## Notes
- All prices are for on-demand/pay-as-you-go instances unless noted
- Prices are in USD
- Major cloud providers offer 8x H200 GPUs per instance
- Specialized providers offer more flexible single-GPU pricing
- Regional pricing may vary for major cloud providers
- Vast.ai offers both spot and on-demand pricing (pricing shown is typical spot rate)
